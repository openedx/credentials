import datetime
from collections import defaultdict
from typing import TYPE_CHECKING, List

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
from credentials.apps.records.utils import get_credentials


if TYPE_CHECKING:
    from credentials.apps.credentials.models import CourseRun

COURSE_CERTIFICATE_CONTENT_TYPE = ContentType.objects.filter(app_label="credentials", model="coursecertificate")


def _does_awarded_program_cert_exist_for_user(program, user):
    """
    A utility function that determines if a (Program) Certificate has been awarded to a learner in a specified program.

    Args:
        program (Program): Program object instance
        user (User): Django User object

    Returns:
        Bool: The returned value represents if the learner has an awarded certificate in the specified program
    """
    program_credential_query = get_user_credentials_by_id(
        user.username, UserCredentialStatus.AWARDED.value, program.uuid
    )
    return program_credential_query.exists()


def _get_transformed_learner_data(user):
    """
    A utility function that extracts user data from the learner's User instance. This data is used to render a piece of
    the Program Record page.

    Args:
        user (User): Django User object

    Returns:
        Dict: A dictionary containing a subset of the learner's User instance data (full name, username, email)
    """
    return {
        "full_name": user.get_full_name(),
        "username": user.username,
        "email": user.email,
    }


def _get_transformed_program_data(program, user, highest_attempt_dict, last_updated):
    """
    A utility function that transforms Program and Program metadata into a dictionary. This data is used to render a
    piece of the Program Record page.

    Args:
        program (Program): Program object instance
        user (User): Django User object
        highest_attempt_dict (Dict): A dict containing a mapping of a learner's courses and the highest grade achieved
            in those courses
        last_updated (DateTime): A DateTime instance representing the last time the Program Record was updated

    Returns:
        Dict: A dictionary representing a subset of Program and related metadata important  rendering a learner's
            Program Record page
    """
    return {
        "name": program.title,
        "type": slugify(program.type),
        "type_name": program.type,
        "completed": _does_awarded_program_cert_exist_for_user(program, user),
        "empty": not highest_attempt_dict,
        "last_updated": last_updated.isoformat(),
        "school": ", ".join(program.authoring_organizations.values_list("name", flat=True)),
    }


def _get_transformed_pathway_data(program, user):
    """
    Gathers and transforms pathway data specific to a learner's status in a given Program.

    Args:
        program (Program): Program object instance
        user (User): Django User object
    """
    program_pathways = program.pathways.all()
    program_pathways_set = frozenset(program_pathways)

    user_credit_pathways = (
        UserCreditPathway.objects.select_related("pathway").filter(user=user, pathway__in=program_pathways_set).all()
    )
    # maps a learner's pathway status to a pathway
    user_credit_pathways_dict = {user_pathway.pathway: user_pathway.status for user_pathway in user_credit_pathways}
    pathways = [(pathway, user_credit_pathways_dict.setdefault(pathway, "")) for pathway in program_pathways]
    # finally, convert the data to a list of dictionaries in the form desired
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

    return pathway_data


def _get_transformed_grade_data(program, user):
    """
    A utility function that gathers and transforms a learner's grade data for course-runs that are part of a Program.
    This data is used to render a learner's Program Record page.

    Args:
        program (Program): Program object instance
        user (User): Django User object

    Returns:
        transformed_grade_data (Dict): A dictionary containing a subset of a learner's grade information for each
            course-run of a specific Program
        highest_attempt_dict (Dict): A dictionary mapping a learner's highest achieved grade in each course of a
            specific Program
        last_updated (DateTime): A DateTime representing the most recent time a learner's grades or certificates were
            updated in a specific Program.
    """
    # creates a Django QuerySet containing the course-runs of the specified program
    program_course_runs = program.course_runs.all()
    # creates an immutable set of course-run data from the above QuerySet
    program_course_runs_set = frozenset(program_course_runs)

    # get all of the learner's course certificates associated with the program courses (including non-AWARDED ones)
    course_user_credentials = get_user_credentials_by_content_type(
        user.username, COURSE_CERTIFICATE_CONTENT_TYPE, status=None
    )
    # create a new dictionary, mapping a course-run id (key) to an associated credential
    user_credential_dict = {
        user_credential.credential.course_run.key: user_credential for user_credential in course_user_credentials
    }
    # maps a credential to its visible_date (a date when the certificate becomes viewable)
    visible_dates = get_credential_dates(course_user_credentials, True)
    # retrieves the learner's grades (from verified course-runs) relevant to this program
    course_grades = UserGrade.objects.select_related("course_run__course").filter(
        username=user.username, course_run__in=program_course_runs_set, verified=True
    )

    # `num_attempts_dict` is used to track how many times a learner has attempted a particular course
    num_attempts_dict = defaultdict(int)
    # `highest_attempt_dict` maps the learner's highest grade earned in a course-run to a course
    highest_attempt_dict = {}
    # `last_updated` tracks the most recent time any certificate or grade was last updated
    last_updated = None

    # find the learner's highest grade for each course, how many times they have taken each course, and keep track of
    # the last time these records were updated
    for course_grade in course_grades:
        course_run = course_grade.course_run
        course = course_run.course

        user_credential = user_credential_dict.get(course_run.key)
        if user_credential:
            num_attempts_dict[course] += 1
            visible_date = visible_dates[user_credential]
            last_updated = max(filter(None, [visible_date, course_grade.modified, last_updated]))

            # find the highest course grade out of all attempts at a course
            if user_credential.status == UserCredentialStatus.AWARDED.value:
                current = highest_attempt_dict.setdefault(course, course_grade)
                if course_grade.percent_grade > current.percent_grade:
                    highest_attempt_dict[course] = course_grade

    last_updated = last_updated or datetime.datetime.today()

    # now, transform this grade data into the format we prefer for our response
    transformed_grade_data = []
    added_courses = set()

    # add the course-run grade data to the response in the order that is maintained by the Program's sorted field
    for course_run in program_course_runs:
        course = course_run.course
        grade = highest_attempt_dict.get(course)

        # if the learner hasn't taken this course yet, or doesn't have a cert, we want to show empty values
        if grade is None and course not in added_courses:
            transformed_grade_data.append(
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
        elif grade is not None and grade.course_run == course_run:
            user_credential = user_credential_dict.get(course_run.key)
            issue_date = get_credential_dates(user_credential, False)
            transformed_grade_data.append(
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

    # In the current implementation of the Program Record page, the Program info is coupled to some of the grade data
    # generated in this function. Previously, all this logic was in a single function and it was hard to follow. While
    # we have refactored this function to be a bit more readable, I still need to pass back `highest_attempt_dict` and
    # `last_updated` to keep some of the existing functionality working. Maybe in the future we get a chance to do a
    # deeper refactor.
    return transformed_grade_data, highest_attempt_dict, last_updated


def _get_shared_program_cert_record_data(program, user):
    """
    A utility function that retrieves the UUID of a shared program record. This data is used to conditionally render
    a component to share vs. copy a Program Record on our frontend.

    Args:
        program (Program): Program object instance
        user (User): Django User object

    Returns:
        String: The UUID of the shared program record converted to a String
    """
    # if a ProgramCertRecord instance is found then return the UUID (as a string), otherwise return None
    try:
        shared_program_record = ProgramCertRecord.objects.get(user=user.id, program=program.id)
    except ProgramCertRecord.DoesNotExist:
        return None
    else:
        return str(shared_program_record.uuid.hex)


def get_program_record_data(user, program_uuid, site, platform_name=None):
    """
    Get all of the data associated with a record by its uuid

    Arguments:
        user(user): Django User object
        program_uuid(str): A Program's unique indentifier, used to retrieve a Program object instance
        site(site): Django site
        platform_name(str): Name of the platform associated with the program record

    Returns:
        Dict: A dictionary containing a subset of learner, program, and grade information used to render our Program
            Record page(s).
    """
    program = get_program_and_course_details(program_uuid, site)

    learner_data = _get_transformed_learner_data(user)
    grade_data, highest_attempt_dict, last_updated = _get_transformed_grade_data(program, user)
    program_data = _get_transformed_program_data(program, user, highest_attempt_dict, last_updated)
    pathway_data = _get_transformed_pathway_data(program, user)
    shared_program_record_uuid = _get_shared_program_cert_record_data(program, user)

    return {
        "learner": learner_data,
        "program": program_data,
        "platform_name": platform_name,
        "grades": grade_data,
        "pathways": pathway_data,
        "shared_program_record_uuid": shared_program_record_uuid,
    }


def get_program_details(request_user, request_site, uuid, is_public):
    """
    Retrieves the details (earned certificates and grade data) of a learner in the specified Program. This utility
    function uses the value of `is_public` to determine if the `uuid` in the function arguments belongs to a Program or
    a shared/public ProgramCertRecord instance.

    Arguments:
        request_user: User from the request (if not public)
        request_site: Site from the request (if not public)
        uuid(str): ID associated with this run of the program
        is_public(bool): Determines whether record can be sent/shared
    Returns:
        Dict: A dictionary of data that will be used to render the Program Record for a learner.
    """
    # If public, the UUID is of a shared ProgramCertRecord instance. If private (is_public == false), the UUID is that
    # of a specific Program.
    if is_public:
        program_cert_record = ProgramCertRecord.objects.get(uuid=uuid)
        user = program_cert_record.user
        program_uuid = program_cert_record.program.uuid
    else:
        user = request_user
        program_uuid = uuid

    data = get_program_record_data(
        user, program_uuid, request_site, platform_name=request_site.siteconfiguration.platform_name
    )

    site_configuration = request_site.siteconfiguration
    records_help_url = site_configuration.records_help_url if site_configuration else ""

    return {
        "record": data,
        "is_public": is_public,
        "uuid": uuid,
        "records_help_url": records_help_url,
    }


def get_learner_course_run_status(username: str, course_ids: List[str], course_runs: List["CourseRun"]):
    """
    Return the status for all of the related course runs related to the courses in
    the course uuid list, plus any course_runs explicitly called out in the course_runs list
    for the given learner.

    Unlike in the context of a UserCredential.course_id, course_id here does literally mean
    the course.uuid, not course_run.key.
    """

    course_credentials, program_credentials = get_credentials(username)  # pylint: disable=unused-variable

    courses = []
    for credential in course_credentials:
        if (course_ids and (str(credential.credential.course_run.course.uuid) in course_ids)) or (
            course_runs
            and (
                (str(credential.credential.course_run.uuid) in course_runs)
                or ((str(credential.credential.course_run.key) in course_runs))
            )
        ):
            # we don't always have the grade, so defend for missing it
            try:
                grade = UserGrade.objects.get(username=username, course_run=credential.credential.course_run)
                course_grade = {
                    "letter_grade": grade.letter_grade,
                    "percent_grade": grade.percent_grade,
                    "verified": grade.verified,
                }
            except UserGrade.DoesNotExist:
                course_grade = None

            cred_status = {
                "course_uuid": str(credential.credential.course_run.course.uuid),
                "course_run": {
                    "uuid": str(credential.credential.course_run.uuid),
                    "key": credential.credential.course_run.key,
                },
                "status": credential.status,
                "type": credential.credential.certificate_type,
                "certificate_available_date": credential.credential.certificate_available_date,
                "grade": course_grade,
            }
            courses.append(cred_status)
    return courses
