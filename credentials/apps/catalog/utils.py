"""Utilities for integration with the catalog service."""

import logging
from urllib.parse import urljoin

from django.db import transaction

from credentials.apps.catalog.models import Course, CourseRun, Organization, Pathway, Program


logger = logging.getLogger(__name__)


class CatalogDataSynchronizer:
    """
    Utility class which can fetch new data from the catalog service, update existing data, create new data, and
    optionally delete out-of-date data.

    Example use:
        synchronizer = CatalogDataSynchronizer(*args)
        synchronizer.fetch_data()
        if delete_data:
            synchronizer.remove_obsolete_data()
    """

    COURSE = "courses"
    COURSE_RUN = "course_runs"
    ORGANIZATION = "organizations"
    PATHWAY = "pathways"
    PROGRAM = "programs"

    def __init__(self, site, api_client, catalog_api_url, page_size=None):
        """
        Constructor

        Arguments:
            site (Site): The site that all fetch models should connect to
            api_client (ApiClient): The client through which all API calls will be made
            catalog_api_url (str): The full URL root of the catalog API to hit (ex. "https://example.com/api/v1/")
            page_size (int): An optional field to denote the number of results per page to retrieve from the API

        Returns:
            CatalogDataSynchronizer: An instance of the class
        """
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
        # This creates a dictionary where the keys are model types (as above) and the values
        # are a set() which contains the stringified UUIDs of every instance of that model
        # type in the database.
        self.existing_data_sets = {
            model: {str(_uuid) for _uuid in queryset.values_list("uuid", flat=True)}
            for (model, queryset) in self.existing_data.items()
        }

    def add_item(self, model_type, value):
        """
        Add an item to the updated data tracker

        Arguments:
            model_type (str): Name of model type we're adding
            value (str): Unique identifier (often UUID) of instance

        Returns:
            None
        """
        self.updated_data_sets[model_type].add(value)

    def fetch_data(self):
        """
        Fetch data from all catalog endpoints and use it to either create or update data in the DB

        Arguments:
            None

        Returns:
            str: A log of the changes to the data. Useful when the caller needs to print (not log) the data to the
                console
        """
        logger.info(f"Copying catalog data for site {self.site.domain}")
        # fetch organizations
        self.fetch_resource(self.ORGANIZATION, self._parse_organization)
        # fetch courses_and_course_runs
        self.fetch_resource(self.COURSE, self._parse_course, extra_request_params={"include_hidden_course_runs": 1})
        # fetch programs
        self.fetch_resource(self.PROGRAM, self._parse_program)
        # fetch pathways
        self.fetch_resource(self.PATHWAY, self._parse_pathway)
        logger.info("Finished copying pathways.")
        return self._log_and_return_changes()

    def remove_obsolete_data(self):
        """
        Remove data that was deleted out of the Discovery service

        Arguments:
            None

        Returns:
            None
        """
        for model_type, dataset in self.existing_data.items():
            removed = self.existing_data_sets[model_type] - self.updated_data_sets[model_type]
            if removed:
                logger.info(f"Removing the following {model_type} UUIDs: {removed}")
                dataset.filter(uuid__in=removed).delete()

    def fetch_resource(self, resource_name, parse_method, extra_request_params=None):
        """
        Generic method to page through the API response and parse each item returned

        Arguments:
            resource_name (str): The resource name on the API e.g. /api/v1/programs/ would be "programs"
            parse_method (func): The method to parse the individual responses with

        Returns:
            None
        """

        if extra_request_params is None:
            extra_request_params = {}

        resource_url = urljoin(self.catalog_api_url, f"{resource_name}/")
        next_page = 1
        while next_page:
            response = self.api_client.get(
                resource_url,
                params=dict({"exclude_utm": 1, "page": next_page, "page_size": self.page_size}, **extra_request_params),
            )
            response.raise_for_status()
            data = response.json()
            for resource in data["results"]:
                logger.info(f'Copying {resource_name} "{resource["uuid"]}"')
                parse_method(resource)

            next_page = next_page + 1 if data["next"] else None

    def _log_and_return_changes(self):
        """
        Log the data that will be added or deleted. Returns the logs as a string for callers that need to print
        (not log) the changes to the console.

        Note: The removed data won't be removed unless remove_obsolete_data() is called.

        Arguments:
            None

        Returns:
            None
        """
        data_diffs = {}
        logger.info("The CatalogDataSynchronizer caused the following changes:")
        for model_type in self.existing_data:
            added = [str(_uuid) for _uuid in self.updated_data_sets[model_type] - self.existing_data_sets[model_type]]
            to_be_removed = [
                str(_uuid) for _uuid in self.existing_data_sets[model_type] - self.updated_data_sets[model_type]
            ]
            if added:
                logger.info(f"{model_type} UUIDs added: {added}")
            if to_be_removed:
                logger.info(f"{model_type} UUIDs to be removed: {to_be_removed}")
            data_diffs[model_type] = {"added": added, "removed": to_be_removed}
        return data_diffs

    @transaction.atomic
    def _parse_organization(self, data):
        """
        Creates or updates an organization. Does not create any relationships or trigger any further parsing.

        Assumes no data has previously been parsed

            Arguments:
                data (dict): The organization data pulled from the API

            Returns:
                Organization: The organization that was created
        """
        org, _ = Organization.objects.update_or_create(
            site=self.site,
            uuid=data["uuid"],
            defaults={
                "key": data["key"],
                "name": data["name"],
                "certificate_logo_image_url": data["certificate_logo_image_url"],
            },
        )
        self.add_item(self.ORGANIZATION, str(org.uuid))

        return org

    @transaction.atomic
    def _parse_program(self, data):
        """
        Creates or updates a program. Does not trigger any further parsing but does link existing organizations and
        course runs based on the program data.

        Assumes the associated organizations and course runs have already been created

        Arguments:
            data (dict): The program data pulled from the API

        Returns:
            Program: The program that was created
        """
        program, _ = Program.objects.update_or_create(
            site=self.site,
            uuid=data["uuid"],
            defaults={
                "title": data["title"],
                "type": data["type"],
                "status": data["status"],
                "type_slug": data["type_attrs"]["slug"],
                "total_hours_of_effort": data["total_hours_of_effort"],
            },
        )
        self.add_item(self.PROGRAM, str(program.uuid))

        program.authoring_organizations.clear()
        for org_data in data["authoring_organizations"]:
            org = Organization.objects.get(site=self.site, uuid=org_data["uuid"])
            program.authoring_organizations.add(org)

        program.course_runs.clear()
        for course_data in data["courses"]:
            for course_run_data in course_data["course_runs"]:
                course_run = CourseRun.objects.get(course__uuid=course_data["uuid"], uuid=course_run_data["uuid"])
                program.course_runs.add(course_run)

        return program

    @transaction.atomic
    def _parse_course(self, data):
        """
        Creates or updates a course and triggers parsing of the course runs

        Assumes the related organizations have already been created

        Arguments:
            data (dict): The course data pulled from the API

        Returns:
            tuple(Course, list(CourseRun)): The Course that was created and a list of all child CourseRuns created
        """
        course, _ = Course.objects.update_or_create(
            site=self.site,
            uuid=data["uuid"],
            defaults={
                "key": data["key"],
                "title": data["title"],
            },
        )

        self.add_item(self.COURSE, str(course.uuid))

        course.owners.clear()
        for org_data in data["owners"]:
            org = Organization.objects.get(site=self.site, uuid=org_data["uuid"])
            course.owners.add(org)

        course_runs = []
        for run_data in data["course_runs"]:
            course_run = self._parse_course_run(course, run_data)
            course.course_runs.add(course_run)
            course_runs.append(course_run)

        # We count course_runs separately, since some programs may not have all runs that a course does
        return course, course_runs

    def _parse_course_run(self, course, data):
        """
        Creates or updates a course run and links it to the course.

        Assumes that the associated programs were created before this is run.

        Arguments:
            course (Course): The course the course run should be linked to
            data (dict): The course run data pulled from the API

        Returns:
            CourseRun: The CourseRun that was created
        """
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
        self.add_item(self.COURSE_RUN, str(course_run.uuid))
        return course_run

    @transaction.atomic
    def _parse_pathway(self, data):
        """
        Creates or updates a pathway and links it to connected programs

        Assumes that the associated programs were parsed before this is run.

        Arguments:
            data (dict): The pathway data pulled from the API

        Returns:
            Pathway: The Pathway that was created
        """
        pathway, _ = Pathway.objects.update_or_create(
            uuid=data["uuid"],
            site=self.site,
            defaults={
                "name": data["name"],
                "email": data["email"],
                "org_name": data["org_name"],
                "status": data["status"],
                "pathway_type": data["pathway_type"],
            },
        )

        self.add_item(self.PATHWAY, str(pathway.uuid))

        pathway.programs.clear()
        for program_data in data["programs"]:
            program = Program.objects.get(site=self.site, uuid=program_data["uuid"])
            pathway.programs.add(program)

        return pathway
