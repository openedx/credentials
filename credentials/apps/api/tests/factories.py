"""
Factories for credential models.
"""
# pylint: disable=missing-docstring

import uuid  # pylint: disable=unused-import

import factory
from django.conf import settings
from django.contrib.sites.models import Site

from credentials.apps.credentials import constants, models


PASSWORD = 'dummy-password'


class SiteFactory(factory.django.DjangoModelFactory):
    class Meta(object):
        model = Site


class CertificateTemplateFactory(factory.django.DjangoModelFactory):
    class Meta(object):
        model = models.CertificateTemplate

    name = factory.Sequence(lambda n: 'template%d' % n)
    content = '<html></html>'


class SiteCertificateTemplateBaseFactory(factory.django.DjangoModelFactory):
    site = factory.SubFactory(SiteFactory)
    template = factory.SubFactory(CertificateTemplateFactory)


class ProgramCertificateFactory(SiteCertificateTemplateBaseFactory):
    class Meta(object):
        model = models.ProgramCertificate

    program_id = factory.Sequence(int)


class CourseCertificateFactory(SiteCertificateTemplateBaseFactory):
    class Meta(object):
        model = models.CourseCertificate

    course_id = factory.Sequence(lambda o: 'course-%d' % o)
    certificate_type = constants.CertificateType.HONOR


class UserCredentialFactory(factory.django.DjangoModelFactory):
    class Meta(object):
        model = models.UserCredential

    credential = factory.SubFactory(ProgramCertificateFactory)
    username = factory.Sequence(lambda o: 'robot%d' % o)
    status = models.UserCredential.AWARDED
    download_url = 'http://www.google.com'
    uuid = factory.LazyAttribute(lambda o: uuid.uuid4())  # pylint: disable=undefined-variable


class UserCredentialAttributeFactory(factory.django.DjangoModelFactory):
    class Meta(object):
        model = models.UserCredentialAttribute

    user_credential = factory.SubFactory(UserCredentialFactory)
    name = factory.Sequence(lambda o: u'name-%d' % o)
    value = factory.Sequence(lambda o: u'value-%d' % o)


class UserFactory(factory.django.DjangoModelFactory):
    username = factory.Sequence(lambda o: 'robot%d' % o)
    email = factory.LazyAttribute(lambda obj: '%s@edx.org' % obj.username)
    first_name = 'robot'
    last_name = 'user'
    password = factory.PostGenerationMethodCall('set_password', PASSWORD)
    is_active = True
    is_superuser = False
    is_staff = False

    class Meta(object):
        model = settings.AUTH_USER_MODEL
