from .data import OrganizationDetails, ProgramDetails
from .models import Program as _Program


def get_program_details_by_uuid(uuid, site):
    try:
        program = _Program.objects.get(uuid=uuid, site=site)
    except _Program.DoesNotExist:
        return None

    return _convert_program_to_program_details(program)


def _convert_program_to_program_details(
    program,
):
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
            certificate_logo_image_url=organization.certificate_logo_image_url
        )
        for organization
        in program_authoring_organizations
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
        status=program.status
    )
