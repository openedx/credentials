"""Utilities for integration with the catalog service."""

from django.db import transaction

from credentials.apps.catalog.models import Course, CourseRun, Organization, Pathway, Program


# Note: these parsing functions don't attempt to clear out old data that is no longer provided by Discovery.
# That shouldn't normally happen (ideally content just gets archived, not deleted).
# Having broken links in our DB would be hard to deal with, so for now, we just leave any old objects around
# and don't worry about matching current Discovery state exactly.

def parse_organization(site, data):
    org, _ = Organization.objects.update_or_create(
        site=site,
        uuid=data['uuid'],
        defaults={
            'key': data['key'],
            'name': data['name'],
            'certificate_logo_image_url': data['certificate_logo_image_url'],
        },
    )
    return org


def parse_course_run(course, data):
    course_run, _ = CourseRun.objects.update_or_create(
        course=course,
        uuid=data['uuid'],
        defaults={
            'key': data['key'],
            'title_override': data['title'] if data['title'] != course.title else None,

            # We are migrating all 'start' and 'end' model fields to include
            # the _date suffix.  During this transition, support both variants
            # provided by the Discovery service. DE-1708.
            # TODO: After updating the Discovery service to send 'start_date'
            # and 'end_date', simplify this logic.
            'start_date': data['start_date'] if 'start_date' in data else data['start'],
            'end_date': data['end_date'] if 'end_date' in data else data['end'],
        },
    )
    return course_run


@transaction.atomic
def parse_course(site, data):
    course, _ = Course.objects.update_or_create(
        site=site,
        uuid=data['uuid'],
        defaults={
            'key': data['key'],
            'title': data['title'],
        },
    )

    course.owners.clear()
    for org_data in data['owners']:
        org = parse_organization(site, org_data)
        course.owners.add(org)

    course_runs = []
    for run_data in data['course_runs']:
        course_run = parse_course_run(course, run_data)
        course.course_runs.add(course_run)
        course_runs.append(course_run)

    # We count course_runs separately, since some programs may not have all runs that a course does
    return course, course_runs


@transaction.atomic
def parse_program(site, data):
    program, _ = Program.objects.update_or_create(
        site=site,
        uuid=data['uuid'],
        defaults={
            'title': data['title'],
            'type': data['type'],
            'status': data['status'],
            'type_slug': data['type_attrs']['slug'],
            'total_hours_of_effort': data['total_hours_of_effort']
        },
    )

    program.authoring_organizations.clear()
    for org_data in data['authoring_organizations']:
        org = parse_organization(site, org_data)
        program.authoring_organizations.add(org)

    program.course_runs.clear()
    for course_data in data['courses']:
        _, course_runs = parse_course(site, course_data)
        program.course_runs.add(*course_runs)

    return program


@transaction.atomic
def parse_pathway(site, data):
    """
    Assumes that the associated programs were parsed before this is run.
    """
    pathway, _ = Pathway.objects.update_or_create(
        uuid=data['uuid'],
        site=site,
        defaults={
            'name': data['name'],
            'email': data['email'],
            'org_name': data['org_name'],
            'pathway_type': data['pathway_type'],
        }
    )

    pathway.programs.clear()
    for program_data in data['programs']:
        program = Program.objects.get(site=site, uuid=program_data['uuid'])
        pathway.programs.add(program)

    return pathway
