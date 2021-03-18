"""Utilities for integration with the catalog service."""
import logging
from urllib.parse import urljoin

from django.db import transaction

from credentials.apps.catalog.models import Course, CourseRun, Organization, Pathway, Program


logger = logging.getLogger(__name__)


class CatalogDataSynchronizer:
    COURSE = "course"
    COURSE_RUN = "course_run"
    ORGANIZATION = "organization"
    PATHWAY = "pathway"
    PROGRAM = "program"

    def __init__(self, site, api_client, catalog_api_url, page_size):
        self.site = site
        self.api_client = api_client
        self.catalog_api_url = catalog_api_url
        self.page_size = page_size
        self.existing_data = {
            self.COURSE: Course.objects.filter(site=site),
            self.COURSE_RUN: CourseRun.objects.filter(course__site=site),
            self.ORGANIZATION: Organization.objects.filter(site=site),
            self.PATHWAY: Pathway.objects.filter(site=site),
            self.PROGRAM: Program.objects.filter(site=site),
        }
        self.updated_data_sets = {
            self.COURSE: set(),
            self.COURSE_RUN: set(),
            self.ORGANIZATION: set(),
            self.PATHWAY: set(),
            self.PROGRAM: set(),
        }
        self.existing_data_sets = {
            model: set(queryset.values_list("uuid", flat=True)) for (model, queryset) in self.existing_data.items()
        }

    def add_item(self, model_type, value):
        self.updated_data_sets[model_type].add(value)

    def fetch_data(self):
        logger.info(f"Copying catalog data for site {self.site.domain}")
        self._fetch_programs()
        logger.info("Finished copying programs.")
        self._fetch_pathways()
        logger.info("Finished copying pathways.")
        self._log_changes()

    def remove_externally_deleted_data(self):
        """Removes data that was deleted out of the Discovery service"""
        for model_type in self.existing_data:
            removed = self.existing_data_sets[model_type] - self.updated_data_sets[model_type]
            if removed:
                logger.info(f"Removing the following {model_type} UUIDs: {removed}")
                self.existing_data[model_type].filter(uuid__in=removed).delete()

    def _fetch_programs(self):
        programs_url = urljoin(self.catalog_api_url, "programs/")
        next_page = 1
        while next_page:
            response = self.api_client.get(
                programs_url, params={"exclude_utm": 1, "page": next_page, "page_size": self.page_size}
            )
            response.raise_for_status()
            programs = response.json()
            for program in programs["results"]:
                logger.info(f'Copying program "{program["title"]}"')
                parse_program(self.site, program, self)

            next_page = next_page + 1 if programs["next"] else None

    def _fetch_pathways(self):
        pathways_url = urljoin(self.catalog_api_url, "pathways/")
        next_page = 1
        while next_page:
            response = self.api_client.get(
                pathways_url, params={"exclude_utm": 1, "page": next_page, "page_size": self.page_size}
            )
            response.raise_for_status()
            pathways = response.json()
            for pathway in pathways["results"]:
                logger.info(f'Copying pathway "{pathway["name"]}"')
                parse_pathway(self.site, pathway, self)
            next_page = next_page + 1 if pathways["next"] else None

    def _log_changes(self):
        """Prints out the what data will be added and what will be deleted"""
        logger.info("The copy_catalog command caused the following changes:")
        for model_type in self.existing_data:
            added = [str(_uuid) for _uuid in self.updated_data_sets[model_type] - self.existing_data_sets[model_type]]
            to_be_removed = [
                str(_uuid) for _uuid in self.existing_data_sets[model_type] - self.updated_data_sets[model_type]
            ]
            if added:
                logger.info(f"{model_type} UUIDs added: {added}")
            if to_be_removed:
                logger.info(f"{model_type} UUIDs to be removed: {to_be_removed if to_be_removed else None}")


@transaction.atomic
def parse_program(site, data, synchronizer=None):
    program, _ = Program.objects.update_or_create(
        site=site,
        uuid=data["uuid"],
        defaults={
            "title": data["title"],
            "type": data["type"],
            "status": data["status"],
            "type_slug": data["type_attrs"]["slug"],
            "total_hours_of_effort": data["total_hours_of_effort"],
        },
    )
    if synchronizer:
        synchronizer.add_item(synchronizer.PROGRAM, program.uuid)

    program.authoring_organizations.clear()
    for org_data in data["authoring_organizations"]:
        org = parse_organization(site, org_data, synchronizer)
        program.authoring_organizations.add(org)

    program.course_runs.clear()
    for course_data in data["courses"]:
        _, course_runs = parse_course(site, course_data, synchronizer)
        program.course_runs.add(*course_runs)

    return program


@transaction.atomic
def parse_course(site, data, synchronizer=None):
    course, _ = Course.objects.update_or_create(
        site=site,
        uuid=data["uuid"],
        defaults={
            "key": data["key"],
            "title": data["title"],
        },
    )

    if synchronizer:
        synchronizer.add_item(synchronizer.COURSE, course.uuid)

    course.owners.clear()
    for org_data in data["owners"]:
        org = parse_organization(site, org_data, synchronizer)
        course.owners.add(org)

    course_runs = []
    for run_data in data["course_runs"]:
        course_run = parse_course_run(course, run_data, synchronizer)
        course.course_runs.add(course_run)
        course_runs.append(course_run)

    # We count course_runs separately, since some programs may not have all runs that a course does
    return course, course_runs


def parse_course_run(course, data, synchronizer=None):
    course_run, _ = CourseRun.objects.update_or_create(
        course=course,
        uuid=data["uuid"],
        defaults={
            "key": data["key"],
            "title_override": data["title"] if data["title"] != course.title else None,
            # We are migrating all 'start' and 'end' model fields to include
            # the _date suffix.  During this transition, support both variants
            # provided by the Discovery service. DE-1708.
            # TODO: After updating the Discovery service to send 'start_date'
            # and 'end_date', simplify this logic.
            "start_date": data["start_date"] if "start_date" in data else data["start"],
            "end_date": data["end_date"] if "end_date" in data else data["end"],
        },
    )
    if synchronizer:
        synchronizer.add_item(synchronizer.COURSE_RUN, course_run.uuid)
    return course_run


def parse_organization(site, data, synchronizer=None):
    org, _ = Organization.objects.update_or_create(
        site=site,
        uuid=data["uuid"],
        defaults={
            "key": data["key"],
            "name": data["name"],
            "certificate_logo_image_url": data["certificate_logo_image_url"],
        },
    )
    if synchronizer:
        synchronizer.add_item(synchronizer.ORGANIZATION, org.uuid)
    return org


@transaction.atomic
def parse_pathway(site, data, synchronizer=None):
    """
    Assumes that the associated programs were parsed before this is run.
    """
    pathway, _ = Pathway.objects.update_or_create(
        uuid=data["uuid"],
        site=site,
        defaults={
            "name": data["name"],
            "email": data["email"],
            "org_name": data["org_name"],
            "pathway_type": data["pathway_type"],
        },
    )

    if synchronizer:
        synchronizer.add_item(synchronizer.PATHWAY, pathway.uuid)

    pathway.programs.clear()
    for program_data in data["programs"]:
        program = Program.objects.get(site=site, uuid=program_data["uuid"])
        pathway.programs.add(program)

    return pathway
