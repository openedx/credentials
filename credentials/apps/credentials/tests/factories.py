import datetime
import uuid
from typing import TYPE_CHECKING, Optional

import factory

from credentials.apps.catalog.tests.factories import ProgramFactory
from credentials.apps.core.tests.factories import SiteFactory
from credentials.apps.credentials import constants, models

if TYPE_CHECKING:
    from credentials.apps.credentials.models import CourseRun


PASSWORD = "dummy-password"


class AbstractCertificateFactory(factory.django.DjangoModelFactory):
    site = factory.SubFactory(SiteFactory)


class CourseCertificateFactory(AbstractCertificateFactory):
    class Meta:
        model = models.CourseCertificate

    certificate_type = constants.CertificateType.HONOR
    is_active = True
    certificate_available_date = None
    course_run: Optional["CourseRun"] = None
    course_id = course_run.key if course_run else factory.Sequence(lambda o: "course-%d" % o)


class ProgramCertificateFactory(AbstractCertificateFactory):
    class Meta:
        model = models.ProgramCertificate

    is_active = True
    program = factory.SubFactory(ProgramFactory)
    program_uuid = factory.SelfAttribute("program.uuid")


class UserCredentialFactory(factory.django.DjangoModelFactory):
    class Meta:
        model = models.UserCredential

    credential = factory.SubFactory(ProgramCertificateFactory)
    username = factory.Sequence(lambda o: "robot%d" % o)
    status = models.UserCredential.AWARDED
    uuid = factory.LazyFunction(uuid.uuid4)


class UserCredentialAttributeFactory(factory.django.DjangoModelFactory):
    class Meta:
        model = models.UserCredentialAttribute

    user_credential = factory.SubFactory(UserCredentialFactory)
    name = factory.Sequence(lambda o: "name-%d" % o)
    value = factory.Sequence(lambda o: "value-%d" % o)


class UserCredentialDateOverrideFactory(factory.django.DjangoModelFactory):
    class Meta:
        model = models.UserCredentialDateOverride

    date = datetime.date(2021, 5, 11)


class SignatoryFactory(factory.django.DjangoModelFactory):
    class Meta:
        model = models.Signatory

    name = factory.Faker("name")
    title = factory.Faker("job")
