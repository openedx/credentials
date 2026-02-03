import logging
import urllib
from typing import TYPE_CHECKING, Any, Dict, List, Tuple

from django.contrib.contenttypes.models import ContentType
from django.template.defaultfilters import slugify
from django.urls import reverse
from edx_ace import Recipient, ace

from credentials.apps.catalog.api import get_filtered_programs
from credentials.apps.catalog.data import ProgramStatus
from credentials.apps.catalog.models import Program
from credentials.apps.core.api import get_user_by_username
from credentials.apps.credentials.api import (
    get_course_certificates_with_ids,
    get_program_certificates_with_ids,
    get_user_credentials_by_content_type,
)
from credentials.apps.credentials.data import UserCredentialStatus
from credentials.apps.records.constants import UserCreditPathwayStatus
from credentials.apps.records.messages import ProgramCreditRequest
from credentials.apps.records.models import ProgramCertRecord, UserCreditPathway

if TYPE_CHECKING:
    from django.contrib.sites.models import Site

    from credentials.apps.credentials.models import UserCredential

logger = logging.getLogger(__name__)


def send_updated_emails_for_program(request, username, program_certificate):
    """
    If the user has previously sent an email to a pathway org, we want to send an updated one when they finish the
    program.  This function is called from the credentials Program Certificate awarding API

    Args:
        request (HttpRequest): The HttpRequest object, used to extract information about the learner's achievement when
         sending an updated Pathway email
        username (string): The username of the user we will send on behalf of
        program_certificate (AbstractCredential[ProgramCertificate]): A ProgramCertificate configuration for a program,
         used to pull program details used in the updated Pathway program email
    """
    site = program_certificate.site
    user = get_user_by_username(username)
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
        logger.debug("ProgramCertRecord for user_uuid %s, program_uuid %s does not exist", user.id, program.uuid)
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


def get_credentials(request_username: str) -> Tuple[List["UserCredential"], List["UserCredential"]]:
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
    return [course_cert.course_run for course_cert in course_certificates]


def get_user_program_data(
    request_username: str,
    request_site: "Site",
    include_empty_programs: bool = False,
    include_retired_programs: bool = False,
) -> List[Dict[str, Any]]:
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
