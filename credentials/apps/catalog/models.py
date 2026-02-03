"""Models governing integration with the catalog service."""

import logging

from django.contrib.sites.models import Site
from django.db import models
from django_extensions.db.models import TimeStampedModel
from sortedm2m.fields import SortedManyToManyField

from credentials.shared.constants import PathwayType

from .data import PathwayStatus, ProgramStatus

logger = logging.getLogger(__name__)


class Organization(TimeStampedModel):
    """
    Organization model.

    .. no_pii: This model has no PII.
    """

    site = models.ForeignKey(Site, on_delete=models.CASCADE)
    uuid = models.UUIDField(blank=False, null=False, verbose_name="UUID")
    key = models.CharField(max_length=255)
    name = models.CharField(max_length=255)
    certificate_logo_image_url = models.CharField(max_length=512, null=True)

    class Meta:
        unique_together = (("site", "uuid"),)

    def __str__(self):
        return self.name


class Course(TimeStampedModel):
    """
    Course model.

    .. no_pii: This model has no PII.
    """

    site = models.ForeignKey(Site, on_delete=models.CASCADE)
    uuid = models.UUIDField(verbose_name="UUID")
    key = models.CharField(max_length=255)
    title = models.CharField(max_length=255, default=None, null=True, blank=True)
    owners = SortedManyToManyField(Organization, blank=True, related_name="owned_courses")

    class Meta:
        unique_together = (("site", "uuid"),)

    def __str__(self):
        return f"{self.id}: {self.key}: {self.title}"


class CourseRun(TimeStampedModel):
    """
    CourseRun model.

    .. no_pii: This model has no PII.
    """

    course = models.ForeignKey(Course, related_name="course_runs", on_delete=models.CASCADE)
    uuid = models.UUIDField(verbose_name="UUID")
    key = models.CharField(max_length=255)
    title_override = models.CharField(
        max_length=255,
        default=None,
        null=True,
        blank=True,
        help_text="Title specific for this run of a course. "
        "Leave this value blank to default to the parent course's title.",
    )
    start_date = models.DateTimeField(null=True, blank=True, db_index=True)
    end_date = models.DateTimeField(null=True, blank=True, db_index=True)

    # Note that we don't have a status field here -- there are only two statuses for CourseRuns: published and
    # unpublished. But unpublished is really used as a 'retired' flag. So in both cases, we want the run.

    class Meta:
        unique_together = (("course", "uuid"),)

    def __str__(self):
        return f"{self.id}: {self.key}: {self.title}"

    @property
    def title(self):
        return self.title_override or self.course.title


class Program(TimeStampedModel):
    """
    Program model.

    .. no_pii: This model has no PII.
    """

    site = models.ForeignKey(Site, on_delete=models.CASCADE)
    uuid = models.UUIDField(verbose_name="UUID")
    title = models.CharField(max_length=255)
    # We store runs not courses, since not all runs of a course are in a program
    course_runs = SortedManyToManyField(CourseRun, related_name="programs")
    authoring_organizations = SortedManyToManyField(Organization, blank=True, related_name="authored_programs")
    type = models.CharField(max_length=32, blank=False, default="")
    type_slug = models.CharField(max_length=32, blank=False, default="")
    total_hours_of_effort = models.PositiveSmallIntegerField(null=True, blank=True)

    ACTIVE = ProgramStatus.ACTIVE.value
    RETIRED = ProgramStatus.RETIRED.value
    DELETED = ProgramStatus.DELETED.value
    UNPUBLISHED = ProgramStatus.UNPUBLISHED.value  # Discovery does give us unpublished programs...
    status = models.CharField(max_length=24, blank=False, default="active")

    class Meta:
        unique_together = (("site", "uuid"),)

    def __str__(self):
        return f"{self.title} ({self.uuid.hex})"


class Pathway(TimeStampedModel):
    """
    Connects an organization and programs to a Pathway.

    Pathways can be credit pathways that represent channels where learners can
    send their records for credit, or professional pathways.

    .. no_pii: This model has no learner PII. The email address used here is the email address associated with the
    pathway itself (such as 'registrar@school.edu'), not with a learner.
    """

    pathway_type = models.CharField(
        max_length=32,
        choices=[(tag.value, tag.value) for tag in PathwayType],
        default=PathwayType.CREDIT.value,
    )
    site = models.ForeignKey(Site, on_delete=models.CASCADE)
    uuid = models.UUIDField(verbose_name="UUID")
    name = models.CharField(max_length=255)
    org_name = models.CharField(max_length=255)
    email = models.EmailField()
    programs = SortedManyToManyField(Program, related_name="pathways")

    status = models.CharField(
        max_length=24,
        choices=[(tag.value, tag.value) for tag in PathwayStatus],
        default=PathwayStatus.PUBLISHED.value,
    )

    class Meta:
        unique_together = (("site", "uuid"),)

    def __str__(self):
        return self.name
