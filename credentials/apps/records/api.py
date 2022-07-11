import datetime
from collections import defaultdict

from django.contrib.contenttypes.models import ContentType
from django.template.defaultfilters import slugify
from django.utils.translation import gettext as _

from credentials.apps.catalog.api import get_program_and_course_details
from credentials.apps.credentials.api import (
    get_credential_dates,
    get_user_credentials_by_content_type,
    get_user_credentials_by_id,
)
from credentials.apps.credentials.data import UserCredentialStatus
from credentials.apps.records.models import ProgramCertRecord, UserCreditPathway, UserGrade


def get_record_data(user, program_uuid, site, platform_name=None):
    """
    Get all of the data associated with a record by its uuid

    Arguments:
        user(user): User data from the request
        program_uuid(str):  Program uuid to find by
        site(site): Django site
        platform_name(str): Name of the platform associated with the program record

    Returns:
        dict(record): A record of the course runs associated with the provided user information and program uuid
    """
    program = get_program_and_course_details(program_uuid, site)
    program_course_runs = program.course_runs.all()
    program_course_runs_set = frozenset(program_course_runs)

    # Get all pathway organizations and their statuses
    program_pathways = program.pathways.all()
    program_pathways_set = frozenset(program_pathways)
    user_credit_pathways = (
        UserCreditPathway.objects.select_related("pathway").filter(user=user, pathway__in=program_pathways_set).all()
    )
    user_credit_pathways_dict = {user_pathway.pathway: user_pathway.status for user_pathway in user_credit_pathways}
    pathways = [(pathway, user_credit_pathways_dict.setdefault(pathway, "")) for pathway in program_pathways]

    # Find program credential if it exists (indicates if user has completed this program)
    program_credential_query = get_user_credentials_by_id(
        user.username, UserCredentialStatus.AWARDED.value, program_uuid
    )

    # Get all of the user course-certificates associated with the program courses (including not AWARDED ones)
    course_certificate_content_type = ContentType.objects.filter(app_label="credentials", model="coursecertificate")

    course_user_credentials = get_user_credentials_by_content_type(
        user.username, course_certificate_content_type, status=None
    )

    # Maps course run key to the associated credential
    user_credential_dict = {
        user_credential.credential.course_id: user_credential for user_credential in course_user_credentials
    }
    # Maps credentials to visible_date datetimes (a date when the cert becomes valid)
    visible_dates = get_credential_dates(course_user_credentials, True)

    # Get all (verified) user grades relevant to this program
    course_grades = UserGrade.objects.select_related("course_run__course").filter(
        username=user.username, course_run__in=program_course_runs_set, verified=True
    )

    # Keep track of number of attempts and best attempt per course
    num_attempts_dict = defaultdict(int)
    highest_attempt_dict = {}  # Maps course -> highest grade earned
    last_updated = None

    # Find the highest course cert grades for each course
    for course_grade in course_grades:
        course_run = course_grade.course_run
        course = course_run.course
        user_credential = user_credential_dict.get(course_run.key)
        if user_credential is not None:
            num_attempts_dict[course] += 1
            visible_date = visible_dates[user_credential]
            last_updated = max(filter(None, [visible_date, course_grade.modified, last_updated]))

            # Update grade if grade is higher and part of awarded cert
            if user_credential.status == UserCredentialStatus.AWARDED.value:
                current = highest_attempt_dict.setdefault(course, course_grade)
                if course_grade.percent_grade > current.percent_grade:
                    highest_attempt_dict[course] = course_grade

    last_updated = last_updated or datetime.datetime.today()

    learner_data = {
        "full_name": user.get_full_name(),
        "username": user.username,
        "email": user.email,
    }

    program_data = {
        "name": program.title,
        "type": slugify(program.type),
        "type_name": program.type,
        "completed": program_credential_query.exists(),
        "empty": not highest_attempt_dict,
        "last_updated": last_updated.isoformat(),
        "school": ", ".join(program.authoring_organizations.values_list("name", flat=True)),
    }

    pathway_data = [
        {
            "name": pathway[0].name,
            "id": pathway[0].id,
            "status": pathway[1],
            "is_active": bool(pathway[0].email),
            "pathway_type": pathway[0].pathway_type,
        }
        for pathway in pathways
    ]
    # Add course-run data to the response in the order that is maintained by the Program's sorted field
    course_data = _get_course_data(program_course_runs, highest_attempt_dict, user_credential_dict, num_attempts_dict)

    return {
        "learner": learner_data,
        "program": program_data,
        "platform_name": platform_name,
        "grades": course_data,
        "pathways": pathway_data,
    }


def _get_course_data(program_course_runs, highest_attempt_dict, user_credential_dict, num_attempts_dict):
    """
    Get course run grade data from the program course runs

    Arguments:
        program_course_runs(QuerySet): List of program course runs
        user_credential_dict(dict): Dict of user credentials
        highest_attempt_dict(dict): Dict for keeping track of the best attempt
        num_attempts_dict(dict): Dict for keeping track of number of attempts

    Returns:
        list(course_data): List of course data
    """
    # Add course-run data to the response in the order that is maintained by the Program's sorted field
    course_data = []
    added_courses = set()
    for course_run in program_course_runs:
        course = course_run.course
        grade = highest_attempt_dict.get(course)

        # If user hasn't taken this course yet, or doesn't have a cert, we want to show empty values
        if grade is None and course not in added_courses:
            course_data.append(
                {
                    "name": course.title,
                    "school": ", ".join(course.owners.values_list("name", flat=True)),
                    "attempts": 0,
                    "course_id": "",
                    "issue_date": "",
                    "percent_grade": 0.0,
                    "letter_grade": "",
                }
            )
            added_courses.add(course)

        # If the user has taken the course, show the course_run info for the highest grade
        elif grade is not None and grade.course_run == course_run:
            user_credential = user_credential_dict.get(course_run.key)
            issue_date = get_credential_dates(user_credential, False)
            course_data.append(
                {
                    "name": course_run.title,
                    "school": ", ".join(course.owners.values_list("name", flat=True)),
                    "attempts": num_attempts_dict[course],
                    "course_id": course_run.key,
                    "issue_date": issue_date.isoformat(),
                    "percent_grade": float(grade.percent_grade),
                    "letter_grade": grade.letter_grade or _("N/A"),
                }
            )
            added_courses.add(course)
    return course_data


def get_program_details(request_user, request_site, uuid, is_public):
    """
    Get details for a program using given ID

    Arguments:
        request_user: User from the request (if not public)
        request_site: Site from the request (if not public)
        uuid(str): ID associated with this run of the program
        is_public(bool): Determines whether record can be sent/shared
    Returns:
        A record associated with this program run
    """
    # if a public view, the uuid is that of a ProgramCertRecord,
    # if private, the uuid is that of a Program
    if is_public:
        program_cert_record = ProgramCertRecord.objects.get(uuid=uuid)
        user = program_cert_record.user
        program_uuid = program_cert_record.program.uuid
    else:
        user = request_user
        program_uuid = uuid

    data = get_record_data(user, program_uuid, request_site, platform_name=request_site.siteconfiguration.platform_name)

    site_configuration = request_site.siteconfiguration
    records_help_url = site_configuration.records_help_url if site_configuration else ""

    return {
        "record": data,
        "is_public": is_public,
        "uuid": uuid,
        "records_help_url": records_help_url,
    }
