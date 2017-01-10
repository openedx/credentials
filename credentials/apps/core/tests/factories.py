"""
Factories for tests of Credentials.
"""
import factory
from django.contrib.sites.models import Site

from credentials.apps.core.models import SiteConfiguration, User

USER_PASSWORD = 'password'


class UserFactory(factory.django.DjangoModelFactory):
    class Meta(object):
        model = User

    username = factory.Sequence(lambda n: 'user_%d' % n)
    password = factory.PostGenerationMethodCall('set_password', USER_PASSWORD)
    first_name = factory.Faker('first_name')
    last_name = factory.Faker('last_name')
    email = factory.Faker('safe_email')
    is_staff = False
    is_active = True


class SiteFactory(factory.django.DjangoModelFactory):
    class Meta(object):
        model = Site


class SiteConfigurationFactory(factory.django.DjangoModelFactory):
    class Meta(object):
        model = SiteConfiguration

    site = factory.SubFactory(SiteFactory)
    lms_url_root = factory.Faker('url')
    catalog_api_url = factory.Faker('url')
