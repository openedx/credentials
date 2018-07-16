"""
Models for the records app.
"""
import uuid

from django.db import models
from django_extensions.db.models import TimeStampedModel

from credentials.apps.catalog.models import CourseRun, Program
from credentials.apps.core.models import User
from credentials.apps.credentials.models import ProgramCertificate


class UserGrade(TimeStampedModel):
    """
    A grade for a specific user and course run
    """
    username = models.CharField(max_length=150, blank=False)
    course_run = models.ForeignKey(CourseRun)
    letter_grade = models.CharField(max_length=255, blank=False)
    percent_grade = models.DecimalField(max_digits=5, decimal_places=4, null=False)
    verified = models.BooleanField(verbose_name='Verified Learner ID', default=True)

    class Meta(object):
        unique_together = ('username', 'course_run')


class ProgramCertRecord(TimeStampedModel):
    """
    Connects a User with a Program
    """
    certificate = models.ForeignKey(ProgramCertificate)
    program = models.ForeignKey(Program, null=True)
    user = models.ForeignKey(User)
    uuid = models.UUIDField(default=uuid.uuid4, editable=False, unique=True)

    def __str__(self):
        return 'ProgramCertificateRecord: {uuid}'.format(uuid=self.uuid)

    class Meta(object):
        unique_together = (('certificate', 'user'),)
        verbose_name = "A viewable record of a program"
