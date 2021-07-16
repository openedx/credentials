from credentials.apps.credentials.utils import filter_visible

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
    user_credentials = filter_visible(
        _UserCredential.objects.filter(
            username=request_username,
            status=status,
            credential_content_type__in=course_cert_content_types,
        )
    )

    return user_credentials
