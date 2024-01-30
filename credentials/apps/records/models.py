"""
Models for the records app.
"""

import uuid

from django.core.exceptions import ValidationError
from django.db import models
from django.utils.translation import gettext_lazy as _
from django_extensions.db.models import TimeStampedModel

from credentials.apps.catalog.models import CourseRun, Pathway, Program
from credentials.apps.core.models import User
from credentials.apps.credentials.models import ProgramCertificate
from credentials.apps.records import constants
from credentials.shared.constants import PathwayType


class UserGrade(TimeStampedModel):
    """
    A grade for a specific user and course run

    .. pii: Stores username for a user.
        pii values: username
    .. pii_types: username
    .. pii_retirement: retained
    """

    username = models.CharField(max_length=150, blank=False)
    course_run = models.ForeignKey(CourseRun, on_delete=models.PROTECT)
    letter_grade = models.CharField(max_length=255, blank=True)
    percent_grade = models.DecimalField(max_digits=5, decimal_places=4, null=False)
    verified = models.BooleanField(verbose_name="Verified Learner ID", default=True)
    lms_last_updated_at = models.DateTimeField(null=True)

    class Meta:
        unique_together = ("username", "course_run")


class ProgramCertRecord(TimeStampedModel):
    """
    Connects a User with a Program

    .. no_pii: This model has no PII.
    """

    certificate = models.ForeignKey(
        ProgramCertificate,
        null=True,
        default=None,
        help_text="Note: certificate is deprecated, and is kept around because it is used in an old data migration.",
        on_delete=models.CASCADE,
    )
    program = models.ForeignKey(Program, on_delete=models.PROTECT)
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    uuid = models.UUIDField(default=uuid.uuid4, editable=False, unique=True)

    def __str__(self):
        return f"ProgramCertificateRecord: {self.uuid}"

    class Meta:
        verbose_name = "Shared program record"
        unique_together = ("program", "user")


class UserCreditPathway(TimeStampedModel):
    """
    Connects a user to a credit pathway
    This is used to track when a user sends a record to that organization
    The timestamp is used for error tracking and support

    .. no_pii: This model has no PII.
    """

    STATUS_CHOICES = [
        (constants.UserCreditPathwayStatus.SENT, _("sent")),
        ("", _("other")),
    ]

    user = models.ForeignKey(User, on_delete=models.CASCADE)
    pathway = models.ForeignKey(Pathway, on_delete=models.PROTECT)
    status = models.CharField(
        max_length=15,
        choices=STATUS_CHOICES,
        default=constants.UserCreditPathwayStatus.SENT,
        blank=True,
    )

    program = models.ForeignKey(Program, null=True, blank=True, on_delete=models.PROTECT)

    def clean(self):
        # Don't allow pathway to have any type other than the CREDIT type
        if self.pathway.pathway_type != PathwayType.CREDIT.value:
            raise ValidationError({"pathway": _("User credit pathways can only be connected to credit pathways.")})

    def save(self, *args, **kwargs):
        self.full_clean()
        return super().save(*args, **kwargs)

    class Meta:
        unique_together = ("user", "pathway", "program")
