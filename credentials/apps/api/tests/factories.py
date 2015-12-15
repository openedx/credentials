"""
Factories for tests of credentials.
"""

import uuid  # pylint: disable=unused-import
import factory

from django.contrib.sites.models import Site

from credentials.apps.credentials import constants
from credentials.apps.credentials import models
from credentials.settings.base import AUTH_USER_MODEL


# pylint: disable=missing-docstring,unnecessary-lambda

PASSWORD = 'dummy-password'


class SiteFactory(factory.django.DjangoModelFactory):
    class Meta(object):
        model = Site

    domain = factory.LazyAttribute(lambda o: 'domain{}.com'.format(o))
    name = factory.LazyAttribute(lambda o: 'name{}'.format(o))


class CertificateTemplateFactory(factory.django.DjangoModelFactory):
    class Meta(object):
        model = models.CertificateTemplate

    name = factory.Sequence(lambda n: 'template{}'.format(n))
    content = factory.LazyAttribute(lambda o: '<html>{}</html>'.format(o))


class SiteCertificateTemplateBaseFactory(factory.django.DjangoModelFactory):
    site = factory.SubFactory(SiteFactory)
    template = factory.SubFactory(CertificateTemplateFactory)
    title = factory.LazyAttribute(lambda o: 'title{}'.format(o))


class ProgramCertificateFactory(SiteCertificateTemplateBaseFactory):
    class Meta(object):
        model = models.ProgramCertificate

    program_id = factory.Sequence(int)


class CourseCertificateFactory(SiteCertificateTemplateBaseFactory):
    class Meta(object):
        model = models.CourseCertificate

    course_id = factory.LazyAttribute(lambda o: 'course{}'.format(o))
    certificate_type = constants.CertificateType.HONOR


class UserCredentialFactory(factory.django.DjangoModelFactory):
    class Meta(object):
        model = models.UserCredential

    credential = factory.SubFactory(ProgramCertificateFactory)
    username = factory.Sequence(lambda o: 'user{}'.format(o))
    status = models.UserCredential.AWARDED
    download_url = factory.LazyAttribute(lambda o: u'http://www.google{0}.com'.format(o))
    uuid = factory.LazyAttribute(lambda o: uuid.uuid4())  # pylint: disable=undefined-variable


class UserCredentialAttributeFactory(factory.django.DjangoModelFactory):
    class Meta(object):
        model = models.UserCredentialAttribute

    user_credential = factory.SubFactory(UserCredentialFactory)
    namespace = factory.LazyAttribute(lambda o: 'whitelabel{}'.format(o))
    name = factory.LazyAttribute(lambda o: 'name{}'.format(o))
    value = factory.LazyAttribute(lambda o: 'value{}'.format(o))


class UserFactory(factory.django.DjangoModelFactory):
    username = factory.Sequence(lambda o: 'robot{}'.format(o))
    email = factory.Sequence(lambda o: u'robot+test+{0}@edx.org'.format(o))
    first_name = 'robot'
    last_name = 'user'
    password = factory.PostGenerationMethodCall('set_password', PASSWORD)
    is_active = True
    is_superuser = False
    is_staff = False

    class Meta(object):
        model = AUTH_USER_MODEL
