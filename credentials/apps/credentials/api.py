from credentials.apps.credentials.utils import filter_visible, get_credential_visible_date, get_credential_visible_dates

from .models import (
    CourseCertificate as _CourseCertificate,
    ProgramCertificate as _ProgramCertificate,
    UserCredential as _UserCredential,
)


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
