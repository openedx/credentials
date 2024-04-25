from typing import List

from .data import OrganizationDetails, ProgramDetails
from .models import CourseRun as _CourseRun, Program as _Program


def get_program_and_course_details(uuid, site):
    """
    Get program and its associated course runs

    Arguments:
        uuid(str): Program uuid to find by
        site(site): Django site

    Returns:
        dict(Program): Program with its course run details
    """
    try:
        program = _Program.objects.prefetch_related("course_runs__course").get(uuid=uuid, site=site)

    except _Program.DoesNotExist:
        return None

    return program


def get_program_details_by_uuid(uuid, site):
    try:
        program = _Program.objects.get(uuid=uuid, site=site)

    except _Program.DoesNotExist:
        return None

    return _convert_program_to_program_details(program)


def _convert_program_to_program_details(program: _Program) -> ProgramDetails:
    """
    Converts a Program (model instance) into a ProgramDetails dataclass.

    Eventually we should move towards a standard portable dataclass that we can
    pass between apps, but this will use the legacy dataclass that the rest
    of the code uses until that time.

    `credential_title` is a empty field which will be overwritten by the
    consuming app that has an override for it. Eventually it should be removed
    from this data.
    """
    program_authoring_organizations = program.authoring_organizations.all()
    program_course_runs = program.course_runs.all()

    organizations = [
        OrganizationDetails(
            uuid=organization.uuid,
            key=organization.key,
            name=organization.name,
            display_name=organization.key,
            certificate_logo_image_url=organization.certificate_logo_image_url,
        )
        for organization in program_authoring_organizations
    ]

    return ProgramDetails(
        uuid=program.uuid,
        title=program.title,
        type=program.type,
        type_slug=program.type_slug,
        credential_title=None,
        course_count=len(program_course_runs),
        organizations=organizations,
        hours_of_effort=program.total_hours_of_effort,
        status=program.status,
    )


def get_course_runs_by_course_run_keys(course_run_keys: List[str]) -> List[_CourseRun]:
    """
    Get course runs using given course run keys

    Arguments:
        course_run_keys (list): List of CourseRun keys

    Returns:
        list(CourseRun): CourseRun objects associated with given course_run_keys
    """
    return _CourseRun.objects.filter(key__in=course_run_keys)


def get_filtered_programs(request_site, allowed_statuses, **course_filters):
    """
    Get programs using given filters

    Arguments:
        request_site(site): Django site to search through
        allowed_statuses(list): List of ProgramStatus values
        course_filters(dict): Filters for courses

    Returns:
        list(Program): Program objects associated with given filters
    """
    programs = (
        _Program.objects.filter(site=request_site, status__in=allowed_statuses, **course_filters)
        .distinct()
        .prefetch_related(
            "authoring_organizations",
            "course_runs",
        )
        .order_by("title")
    )
    return programs
