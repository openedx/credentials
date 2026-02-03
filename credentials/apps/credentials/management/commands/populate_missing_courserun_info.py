"""
Django managment command to sync missing course_run_ids from the catalog
course_run table.
"""

import logging
from typing import TYPE_CHECKING

from django.core.management.base import BaseCommand

from credentials.apps.catalog.api import get_course_runs_by_course_run_keys
from credentials.apps.credentials.models import CourseCertificate

if TYPE_CHECKING:
    from credentials.apps.catalog.models import CourseRun


logger = logging.getLogger(__name__)


class Command(BaseCommand):
    def add_arguments(self, parser):
        parser.add_argument("--verbose", action="store_true", help="Log each update")
        parser.add_argument("--dry_run", action="store_true", help="Don't actually change the data")

    def handle(self, *args, **options):
        """
        Update the course_id from course certificates that are missing it
        as long as the course run is already in the catalog.course_run table.
        """
        course_certificates_without_course_run_id = CourseCertificate.objects.filter(course_run_id=None)
        count = course_certificates_without_course_run_id.count()
        verbosity = options.get("verbose")  # type: bool
        dry_run = options.get("dry_run")  # type: bool
        count_ignored = 0  # type: int

        logger.info(f"Start processing {count} CourseCertificates with no course_id")

        # Because CourseCertificate.course_id isn't a ForeignKey, there's no
        # completely graceful way to join the table with catalog.CourseRun.
        # However, the list of these CourseCertificate object should be small,
        # so the mild time waste of looping through them for occasional
        # on-demand runs of this command is probably better than writing an
        # objects.raw SQL query.
        for course_cert in course_certificates_without_course_run_id:
            course_run_key = course_cert.course_id

            course_runs = get_course_runs_by_course_run_keys([course_run_key])

            if course_runs:
                self.update_course_certificate_with_course_run_id(
                    course_cert,
                    course_runs[0],
                    verbosity,
                    dry_run,
                )
            else:
                # This is fine, and can happen with some frequency
                count_ignored += 1
                if verbosity:
                    logger.info(f"No Catalog.CourseRun entry for {course_run_key}")

        logger.info(f"populate_missing_courserun_info finished! {count_ignored} CourseCertificate(s) safely ignored.")

    def update_course_certificate_with_course_run_id(
        self,
        course_certificate: CourseCertificate,
        course_run: "CourseRun",
        verbosity: bool,
        dry_run: bool,
    ) -> None:
        """Update course_run_id from catalog.CourseRun"""
        if course_run.key:
            course_certificate.course_run = course_run
            dry_run_msg = "(dry run) " if dry_run else ""
            if verbosity:
                logger.info(
                    f"{dry_run_msg}updating CourseCertificate {course_certificate.id} (course_id "
                    f"{course_certificate.course_id}) with course_run_id {course_run.key}"
                )
            # use update_fields to just update this one piece of data
            if not dry_run:
                course_certificate.save(update_fields=["course_run"])
