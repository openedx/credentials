"""
Models for the records app.
"""
import uuid

from django.db import models
from django.utils.translation import ugettext_lazy as _
from django_extensions.db.models import TimeStampedModel

from credentials.apps.catalog.models import CourseRun, CreditPathway, Pathway, Program
from credentials.apps.core.models import User
from credentials.apps.credentials.models import ProgramCertificate
from credentials.apps.records import constants


class UserGrade(TimeStampedModel):
    """
    A grade for a specific user and course run
    """
    username = models.CharField(max_length=150, blank=False)
    course_run = models.ForeignKey(CourseRun)
    letter_grade = models.CharField(max_length=255, blank=True)
    percent_grade = models.DecimalField(max_digits=5, decimal_places=4, null=False)
    verified = models.BooleanField(verbose_name='Verified Learner ID', default=True)

    class Meta(object):
        unique_together = ('username', 'course_run')


class ProgramCertRecord(TimeStampedModel):
    """
    Connects a User with a Program
    """
    certificate = models.ForeignKey(
        ProgramCertificate,
        null=True,
        default=None,
        help_text='Note: certificate is deprecated, and is kept around because it is used in an old data migration.'
    )
    program = models.ForeignKey(Program)
    user = models.ForeignKey(User)
    uuid = models.UUIDField(default=uuid.uuid4, editable=False, unique=True)

    def __str__(self):
        return 'ProgramCertificateRecord: {uuid}'.format(uuid=self.uuid)

    class Meta(object):
        verbose_name = "Shared program record"


class UserCreditPathway(TimeStampedModel):
    """
    Connects a user to a credit pathway
    This is used to track when a user sends a record to that organization
    The timestamp is used for error tracking and support
    """
    STATUS_CHOICES = [
        (constants.UserCreditPathwayStatus.SENT, _('sent')),
        ('', _('other')),
    ]

    user = models.ForeignKey(User)
    credit_pathway = models.ForeignKey(CreditPathway)
    pathway = models.ForeignKey(Pathway, null=True)
    status = models.CharField(
        max_length=15,
        choices=STATUS_CHOICES,
        default=constants.UserCreditPathwayStatus.SENT,
        blank=True,
    )

    class Meta(object):
        unique_together = ('user', 'credit_pathway')
