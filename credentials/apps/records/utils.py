import logging
import urllib

from django.conf import settings
from django.contrib.contenttypes.models import ContentType
from django.template.defaultfilters import slugify
from django.urls import reverse
from edx_ace import Recipient, ace

from credentials.apps.catalog.api import get_course_runs_by_course_run_keys, get_filtered_programs
from credentials.apps.catalog.data import ProgramStatus
from credentials.apps.catalog.models import Program
from credentials.apps.core.models import User
from credentials.apps.credentials.api import (
    get_course_certificates_with_ids,
    get_program_certificates_with_ids,
    get_user_credentials_by_content_type,
)
from credentials.apps.credentials.data import UserCredentialStatus
from credentials.apps.records.constants import UserCreditPathwayStatus
from credentials.apps.records.messages import ProgramCreditRequest
from credentials.apps.records.models import ProgramCertRecord, UserCreditPathway


logger = logging.getLogger(__name__)


def send_updated_emails_for_program(request, username, program_certificate):
    """If the user has previously sent an email to a pathway org, we want to send
    an updated one when they finish the program.  This function is called from the
    credentials Program Certificate awarding API"""
    site = program_certificate.site
    user = User.objects.get(username=username)
    program_uuid = program_certificate.program_uuid

    program = Program.objects.prefetch_related("pathways").get(site=site, uuid=program_uuid)
    pathways_set = frozenset(program.pathways.all())

    user_pathways = UserCreditPathway.objects.select_related("pathway").filter(
        user=user, pathway__in=pathways_set, status=UserCreditPathwayStatus.SENT
    )

    # Return here if the user doesn't have a program cert record
    try:
        pcr = ProgramCertRecord.objects.get(program=program, user=user)
    except ProgramCertRecord.DoesNotExist:
        logger.exception("Program Cert Record for user_uuid %s, program_uuid %s does not exist", user.id, program.uuid)
        return

    # Send emails for those already marked as "SENT"
    for user_pathway in user_pathways:
        pathway = user_pathway.pathway
        record_path = reverse("records:public_programs", kwargs={"uuid": pcr.uuid.hex})
        record_link = request.build_absolute_uri(record_path)
        csv_link = urllib.parse.urljoin(record_link, "csv")

        msg = ProgramCreditRequest(site, user.email).personalize(
            recipient=Recipient(lms_user_id=None, email_address=pathway.email),
            language=program_certificate.language,
            user_context={
                "pathway_name": pathway.name,
                "program_name": program.title,
                "record_link": record_link,
                "user_full_name": user.get_full_name(),
                "program_completed": True,
                "previously_sent": True,
                "csv_link": csv_link,
            },
        )
        ace.send(msg)


def masquerading_authorized(masquerader, target):
    """
    Checks whether a user has the permissions to masquerade as the target user.

    Overrides django-hijack's default authorization function to prevent
    superusers from masquerading as other superusers.

    By default only superusers are allowed to masquerade, unless
    HIJACK_AUTHORIZE_STAFF is enabled in settings.

    By default, staff are not able to masquerade as staff unless
    HIJACK_AUTHORIZE_STAFF_TO_HIJACK_STAFF is enabled in settings.

    Adapted from:
    https://github.com/arteria/django-hijack/blob/4dd897761952adf387fb71822e3e76bc3d0deb51/hijack/helpers.py#L77
    """
    if target.is_superuser:
        return False

    if masquerader.is_superuser:
        return True

    if masquerader.is_staff and getattr(settings, "HIJACK_AUTHORIZE_STAFF", False):
        if target.is_staff and not getattr(settings, "HIJACK_AUTHORIZE_STAFF_TO_HIJACK_STAFF", False):
            return False

        return True

    return False


def get_credentials(request_username):
    """
    Returns two lists of credentials: a course list and a program list

    Arguments:
        request_username(str): Username for whom we are getting UserCredential objects for

    Returns:
        list(course_credentials): A list of course UserCredential objects
        list(program_credentials): A list of program UserCredential objects
    """
    # Get the content types for course and program certs, query for both in single query
    course_cert_content_types = ContentType.objects.filter(
        app_label="credentials", model__in=["coursecertificate", "programcertificate"]
    )
    course_certificate_type = None
    program_certificate_type = None
    for course_cert_content_type in course_cert_content_types:
        if course_cert_content_type.model == "coursecertificate":
            course_certificate_type = course_cert_content_type
        elif course_cert_content_type.model == "programcertificate":
            program_certificate_type = course_cert_content_type

    # Get all user credentials, then sort them out to course/programs
    user_credentials = get_user_credentials_by_content_type(
        request_username, course_cert_content_types, UserCredentialStatus.AWARDED.value
    )
    course_credentials = []
    program_credentials = []
    for credential in user_credentials:
        if credential.credential_content_type_id == course_certificate_type.id:
            course_credentials.append(credential)
        elif credential.credential_content_type_id == program_certificate_type.id:
            program_credentials.append(credential)

    return course_credentials, program_credentials


def _course_credentials_to_course_runs(request_site, course_credentials):
    """
    Convert a list of course UserCredentials into a list of CourseRun objects

    Arguments:
        request_site(site): Django site to search through
        course_credentials(list): A list of course UserCredential objects

    Returns:
        list(CourseRun): The CourseRun objects associated with given credentials
    """
    # Using the course credentials, get the programs associated with them via course runs
    course_credential_ids = [
        x.credential_id for x in course_credentials if x.status == UserCredentialStatus.AWARDED.value
    ]
    course_certificates = get_course_certificates_with_ids(course_credential_ids, request_site)
    course_run_keys = [course_cert.course_id for course_cert in course_certificates]
    return get_course_runs_by_course_run_keys(course_run_keys)


def get_user_program_data(request_username, request_site, include_empty_programs=False, include_retired_programs=False):
    """
    Translates a list of Program and UserCredentials (for programs) into context data.

    Arguments:
        request_username(str): Username for whom we are getting UserCredential objects for
        request_site(site): Django site to search through
        include_empty_programs(bool): If true, empty programs are included, otherwise not included
        include_retired_programs(bool): If true, retired programs are included, otherwise not included

    Returns:
        list(dict): A list of dictionaries, each dictionary containing information for a program that the
        user is enrolled in
    """
    # Get all user credentials
    course_credentials, program_credentials = get_credentials(request_username)

    # Get course runs that this user has a credential in
    course_runs = frozenset(_course_credentials_to_course_runs(request_site, course_credentials))
    course_filters = {} if include_empty_programs else {"course_runs__in": course_runs}

    allowed_statuses = [ProgramStatus.ACTIVE.value]
    if include_retired_programs:
        allowed_statuses.append(ProgramStatus.RETIRED.value)

    # Get a list of programs
    programs = get_filtered_programs(request_site, allowed_statuses, **course_filters)

    # Get the completed programs and a UUID set using the program_credentials
    program_credential_ids = [program_credential.credential_id for program_credential in program_credentials]
    program_certificates = get_program_certificates_with_ids(program_credential_ids, request_site)
    completed_program_uuids = frozenset(
        program_certificate.program_uuid for program_certificate in program_certificates
    )

    return [
        {
            "name": program.title,
            "partner": ", ".join(program.authoring_organizations.values_list("name", flat=True)),
            "uuid": program.uuid.hex,
            "type": slugify(program.type),
            "completed": program.uuid in completed_program_uuids,
            "empty": not bool(course_runs.intersection(frozenset(program.course_runs.all()))),
        }
        for program in programs
    ]
