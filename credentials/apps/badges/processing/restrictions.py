"""Badge issuance restriction checks."""

import logging

import requests
from django.conf import settings
from django.core.exceptions import ObjectDoesNotExist

from credentials.apps.badges.models import CredlyBadgeTemplate
from credentials.apps.core.models import SiteConfiguration

logger = logging.getLogger(__name__)


def is_badge_issuance_allowed(username, badge_template_id, progress):
    """
    Check whether badge issuance is allowed for the completed badge progress.

    The check is disabled by default. When enabled, each fulfillment with a
    course key is validated against the configured restrictions API.

    Badge issuance is blocked only when an exact course match explicitly
    disables the configured badge flag. Missing data or API errors allow
    issuance by default.
    """
    if not getattr(settings, "BADGES_ENABLE_ISSUANCE_RESTRICTIONS", False):
        return True

    if not progress:
        return True

    try:
        badge_template = CredlyBadgeTemplate.objects.get(id=badge_template_id)
        site_configuration = SiteConfiguration.objects.get(site=badge_template.site)
        api_client = site_configuration.api_client
    except ObjectDoesNotExist:
        logger.exception(
            "Unable to load SiteConfiguration for badge template %s. Badge issuance will be allowed by default.",
            badge_template_id,
        )
        return True

    fulfillments = progress.fulfillment_set.all()
    restrictions_api_url = getattr(
        settings,
        "BADGES_ISSUANCE_RESTRICTIONS_API_URL",
        "",
    )
    restriction_flag_name = getattr(
        settings,
        "BADGES_ISSUANCE_RESTRICTIONS_FLAG_NAME",
        "",
    )

    for fulfillment in fulfillments:
        if not fulfillment.course_key:
            continue

        course_key = str(fulfillment.course_key)

        try:
            response = api_client.get(
                restrictions_api_url,
                params={"ccx_id": course_key},
                timeout=5,
            )
        except requests.RequestException:
            logger.exception(
                "Error checking badge issuance restrictions for course %s.",
                course_key,
            )
            continue

        if response.status_code != 200:
            logger.warning(
                "Restrictions API returned status %s for course %s.",
                response.status_code,
                course_key,
            )
            continue

        try:
            response_data = response.json()
        except ValueError:
            logger.warning(
                "Restrictions API returned invalid JSON for course %s.",
                course_key,
            )
            continue

        results = response_data.get("results", [])

        matched_result = next(
            (result for result in results if result.get("ccx_id") == course_key),
            None,
        )

        if not matched_result:
            logger.warning(
                "No exact restriction result found for course %s. Badge issuance will be allowed by default.",
                course_key,
            )
            continue

        allow_badges = matched_result.get(
            restriction_flag_name,
            True,
        )

        if not allow_badges:
            logger.info(
                "Badge issuance blocked for user %s and course %s.",
                username,
                course_key,
            )
            return False

    return True
