import uuid

import factory

from credentials.apps.core.tests.factories import SiteFactory
from credentials.apps.credentials import constants, models


PASSWORD = 'dummy-password'


class AbstractCertificateFactory(factory.django.DjangoModelFactory):
    site = factory.SubFactory(SiteFactory)


class CourseCertificateFactory(AbstractCertificateFactory):
    class Meta:
        model = models.CourseCertificate

    course_id = factory.Sequence(lambda o: 'course-%d' % o)
    certificate_type = constants.CertificateType.HONOR
    is_active = True


class ProgramCertificateFactory(AbstractCertificateFactory):
    class Meta:
        model = models.ProgramCertificate

    is_active = True
    program_uuid = factory.LazyFunction(uuid.uuid4)


class UserCredentialFactory(factory.django.DjangoModelFactory):
    class Meta:
        model = models.UserCredential

    credential = factory.SubFactory(ProgramCertificateFactory)
    username = factory.Sequence(lambda o: 'robot%d' % o)
    status = models.UserCredential.AWARDED
    download_url = factory.Faker('url')
    uuid = factory.LazyFunction(uuid.uuid4)


class UserCredentialAttributeFactory(factory.django.DjangoModelFactory):
    class Meta:
        model = models.UserCredentialAttribute

    user_credential = factory.SubFactory(UserCredentialFactory)
    name = factory.Sequence(lambda o: 'name-%d' % o)
    value = factory.Sequence(lambda o: 'value-%d' % o)


class SignatoryFactory(factory.django.DjangoModelFactory):
    class Meta:
        model = models.Signatory

    name = factory.Faker('name')
    title = factory.Faker('job')
