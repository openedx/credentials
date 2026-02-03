"""
Python API utility functions exposed by the `credentials` Django app.
"""

import logging
from typing import TYPE_CHECKING, Optional

from django.contrib.contenttypes.models import ContentType

from credentials.apps.catalog.api import get_course_runs_by_course_run_keys
from credentials.apps.credentials.models import (
    CourseCertificate as _CourseCertificate,
    ProgramCertificate as _ProgramCertificate,
    UserCredential as _UserCredential,
)
from credentials.apps.credentials.utils import filter_visible, get_credential_visible_date, get_credential_visible_dates

if TYPE_CHECKING:
    from django.contrib.sites.models import Site

    from credentials.apps.catalog.models import CourseRun


logger = logging.getLogger(__name__)


def _get_course_run(course_run_key):
    """
    A utility function that wraps the `get_course_runs_by_course_run_keys` function from the Catalog Python API. If the
    returned query set yields a result then we pass back that course run instance, otherwise we log a warning.

    Arguments:
        course_run_key (String): The course run key we are trying to retrieve

    Returns:
        course_run (CourseRun): The course run instance requested (or None)
    """
    course_run = None

    logger.info(f"Attempting to retrieve course run with key [{course_run_key}]")
    results = get_course_runs_by_course_run_keys([course_run_key])
    # `get_course_runs_by_course_run_keys` returns a query set, ensure we have results and that there is just one match
    if results and results.count() == 1:
        course_run = results[0]
    else:
        logger.warning(f"Could not retrieve a course run with key [{course_run_key}]")

    return course_run


def _update_or_create_credential(username, credential_type, credential_id, status):
    """
    A utility function responsible for issuing (or updating) a UserCredential (certificate) to a learner.

    Args:
        username (String): The username of the user the credential should be issued to
        credential_type (CourseCertificate OR ProgramCertificate): The credential type we are issuing
        credential_id (Int): The id number of the (Program or Course) Certificate Configuration we are issuing
        status (String): The status of the credential (e.g. "awarded" or "revoked")

    Returns:
        credentials (UserCredential): The issued or updated credential
        created (Boolean): A boolean describing if the record was created or updated
    """
    try:
        content_type = ContentType.objects.get_for_model(credential_type)
        credential, created = _UserCredential.objects.update_or_create(
            username=username,
            credential_content_type=content_type,
            credential_id=credential_id,
            defaults={"status": status},
        )
    except Exception:
        logger.exception(
            f"Error occurred processing a credential with credential_id [{credential_id}] for user [{username}]"
        )
        return None, None
    else:
        logger.info(
            f"Processed credential update for user [{username}] with status [{status}]. UUID: [{credential.uuid}], "
            f"created: [{created}]"
        )
        return credential, created


def get_course_cert_config(course_run: "CourseRun", mode: str, create: bool = False) -> Optional[_CourseCertificate]:
    """
    A utility function that attempts to retrieve a course certificate configuration from the provided course run
    instance. Optionally attempts to create a course certificate configuration if one does not exist.

    Arguments:
        course_run (CourseRun): The CourseRun instance
        mode (String): The "mode" of the course run provided (e.g. `verified`, `honor`, `masters`, etc.)
        create (Boolean): A boolean that controls whether we should attempt to create a cert config if one doesn't exist

    Returns:
        course_cert_config (CourseCertificate): The retrieved (or created) CourseCertificate instance
    """
    course_cert_config = None
    try:
        logger.info(f"Attempting to retrieve the course certificate configuration for course run [{course_run.key}]")
        course_cert_config = _CourseCertificate.objects.get(course_id=course_run.key)
    except _CourseCertificate.DoesNotExist:
        logger.warning(f"A course certificate configuration could not be found for course run [{course_run.key}]")
    finally:
        if not course_cert_config and create:
            course_cert_config = create_course_cert_config(course_run, course_run.course.site, mode)

    return course_cert_config


def create_course_cert_config(course_run: "CourseRun", site: "Site", mode: str):
    """
    A utility function that attempts to create a CourseCertificate instance from the provided data.

    Arguments:
        course_run (CourseRun): The course run associated with the CourseCertificate instance to be created
        site (Site): The site associated with the course run
        mode (String): The "certificate type" of the CourseCertificate (e.g. verified, honor, etc.)

    Returns:
        course_cert_config (CourseCertificate): The CourseCertificate instance created
    """
    logger.info(f"Creating a course certificate configuration for course run [{course_run.key}]")

    course_cert_config = None
    try:
        course_cert_config = _CourseCertificate.objects.create(
            course_id=course_run.key, course_run=course_run, site=site, is_active=True, certificate_type=mode
        )
    except Exception:
        logger.exception(f"Error occurred creating a CourseCertificate configuration for course run [{course_run.key}]")

    return course_cert_config


def get_course_certificates_with_ids(course_credential_ids, request_site):
    """
    Get course certificates using given course credential IDs

    Arguments:
        course_credential_ids(list): List of IDs associated with course UserCredential objects
        request_site(site): Django site to search through

    Returns:
        list(CourseCertificate): The CourseCertificate objects associated with given course credential IDs
    """
    return _CourseCertificate.objects.filter(id__in=course_credential_ids, site=request_site)


def get_program_certificates_with_ids(program_credential_ids, request_site):
    """
    Get program certificates using given program credential IDs

    Arguments:
        program_credential_ids(list): List of IDs associated with program UserCredential objects
        request_site(site): Django site to search through

    Returns:
        list(ProgramCertificate): The ProgramCertificate objects associated with given program credential IDs
    """
    return _ProgramCertificate.objects.filter(id__in=program_credential_ids, site=request_site)


def get_user_credentials_by_id(request_username, status, program_uuid):
    """
    Get the user credentials by program id

    Arguments:
        request_username(str): Username for whom we are getting UserCredential objects for
        status(str): Status for a UserCredential
        program_uuid(ID): unique identifier for the desired program

    Returns:
        list(UserCredential): The UserCredential objects associated with given filters
    """
    user_credentials = filter_visible(
        _UserCredential.objects.filter(
            username=request_username, status=status, program_credentials__program_uuid=program_uuid
        )
    )

    return user_credentials


def get_user_credentials_by_content_type(request_username, course_cert_content_types, status):
    """
    Get user credentials by given filters

    Arguments:
        request_username(str): Username for whom we are getting UserCredential objects for
        course_cert_content_types(list): List of content types for a certificate
        status(str): Status for a UserCredential

    Returns:
        list(UserCredential): The UserCredential objects associated with given filters
    """
    if status:
        user_credentials = filter_visible(
            _UserCredential.objects.filter(
                username=request_username,
                status=status,
                credential_content_type__in=course_cert_content_types,
            )
        )
    else:
        user_credentials = filter_visible(
            _UserCredential.objects.prefetch_related("credential").filter(
                username=request_username,
                credential_content_type__in=course_cert_content_types,
            )
        )

    return user_credentials.distinct()


def get_credential_dates(user_credentials, many):
    """
    Get visible credential dates or single date depending on 'many' arugment

    Arguments:
        user_credentials(list): List of user credential(s)
        many(bool): Determines whether to look for dates of many credentials or just a single one

    Returns:
        dict(DateTime): Returns a dictionary of DateTimes keyed by UserCredential
    """
    if many:
        return get_credential_visible_dates(user_credentials)
    else:
        return get_credential_visible_date(user_credentials, use_date_override=True)


def process_course_credential_update(user, course_run_key: str, mode: str, credential_status: str) -> None:
    """
    A utility function responsible for creating or updating a course credential associated with a learner. Primarily
    used when consuming events from the Event Bus.

    Args:
        user (User): The user the credential is being awared to (or revoked from)
        course_run_key (String): The credential's course run key it is associated with
        mode (String): The "certificate type" of the credential. This is the _really_ the "mode" of the course run
         (e.g. "verified", etc.)
        credential_status (String): The desired status of the credential ("awarded" or "revoked")
    """
    course_run = _get_course_run(course_run_key)
    if course_run:
        # Check if a course certificate configuration exists before we attempt to award or revoke the credential. We
        # cannot process a credential update if this configuration doesn't exist. If one doesn't exist, try to create
        # one on the fly (this tracks with legacy behavior when awarding credentials through the REST API pathway).
        course_cert_config = get_course_cert_config(course_run, mode, create=True)
        if course_cert_config:
            _update_or_create_credential(user.username, _CourseCertificate, course_cert_config.id, credential_status)
        else:
            logger.error(
                f"Error updating credential for user [{user.id}] in course run [{course_run_key}] with status "
                f"[{credential_status}]. A course certificate configuration could not be found or created."
            )
            return
    else:
        logger.error(
            f"Error updating credential for user [{user.id}] with status [{credential_status}]. A course run could not "
            f"be found with key [{course_run_key}]."
        )
        return
