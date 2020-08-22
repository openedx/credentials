import datetime
import logging
from itertools import groupby

from django.db.models import Q

from credentials.apps.credentials.models import UserCredentialAttribute

log = logging.getLogger(__name__)

VISIBLE_DATE_FORMAT = "%Y-%m-%dT%H:%M:%SZ"


def to_language(locale):
    if locale is None:
        return None
    # Convert to bytes to get ascii-lowercasing, to avoid the Turkish I problem.
    return locale.replace("_", "-").encode().lower().decode()


def validate_duplicate_attributes(attributes):
    """
    Validate the attributes data

    Arguments:
        attributes (list): List of dicts contains attributes data

    Returns:
        Boolean: Return True only if data has no duplicated namespace and name

    """

    def keyfunc(attribute):
        return attribute["name"]

    sorted_data = sorted(attributes, key=keyfunc)
    for __, group in groupby(sorted_data, key=keyfunc):
        if len(list(group)) > 1:
            return False
    return True


def datetime_from_visible_date(date):
    """ Turn a string version of a datetime, provided to us by the LMS in a particular format it uses for
        visible_date attributes, and turn it into a datetime object. """
    try:
        parsed = datetime.datetime.strptime(date, VISIBLE_DATE_FORMAT)
        # The timezone is always UTC (as indicated by the Z). It looks like in python3.7, we could
        # just use %z instead of replacing the tzinfo with a UTC value.
        return parsed.replace(tzinfo=datetime.timezone.utc)
    except ValueError as e:
        log.exception("%s", e)
        return None


def filter_visible(qs):
    """ Filters a UserCredentials queryset by excluding credentials that aren't supposed to be visible yet. """
    # The visible_date attribute holds a string value, not a datetime one. But we can compare as a string
    # because the format is so strict - it will still lexically compare as less/greater-than.
    nowstr = datetime.datetime.now(datetime.timezone.utc).strftime(VISIBLE_DATE_FORMAT)
    return qs.filter(
        Q(attributes__name="visible_date", attributes__value__lte=nowstr)
        | ~Q(attributes__name="visible_date")
    )


def get_credential_visible_dates(user_credentials):
    """
    Calculates visible date for a collection of UserCredentials.
    Returns a dictionary of {UserCredential: datetime}.
    Guaranteed to return a datetime object for each credential.
    """

    visible_dates = UserCredentialAttribute.objects.prefetch_related(
        "user_credential__credential"
    ).filter(user_credential__in=user_credentials, name="visible_date")

    visible_date_dict = {
        visible_date.user_credential: datetime_from_visible_date(visible_date.value)
        for visible_date in visible_dates
    }

    for user_credential in user_credentials:
        current = visible_date_dict.get(user_credential)
        if current is None:
            visible_date_dict[user_credential] = user_credential.created

    return visible_date_dict


def get_credential_visible_date(user_credential):
    """ Simpler, one-credential version of get_credential_visible_dates. """
    return get_credential_visible_dates([user_credential])[user_credential]
