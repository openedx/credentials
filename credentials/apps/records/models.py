"""
Models for the records app.
"""
from django.db import models
from django_extensions.db.models import TimeStampedModel

from credentials.apps.catalog.models import CourseRun
from credentials.apps.core.models import User
from credentials.apps.credentials import constants


def _choices(*values):
    """
    Helper for use with model field 'choices'.
    """
    return [(value,) * 2 for value in values]


class UserGrade(TimeStampedModel):
    """
    A grade for a specific user and course run
    """
    user = models.ForeignKey(User)
    course_run = models.ForeignKey(CourseRun)
    letter_grade = models.CharField(max_length=255, blank=False)
    percent_grade = models.DecimalField(max_digits=5, decimal_places=4, null=False)
    mode = models.CharField(
        max_length=255,
        blank=False,
        choices=_choices(
            constants.CertificateType.HONOR,
            constants.CertificateType.PROFESSIONAL,
            constants.CertificateType.VERIFIED
        )
    )

    class Meta(object):
        unique_together = ('user', 'course_run')
