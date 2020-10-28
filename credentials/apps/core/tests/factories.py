"""
Factories for tests of Credentials.
"""
from django.contrib.sites.models import Site
from factory import Faker, PostGenerationMethodCall, Sequence, SubFactory, django

from credentials.apps.core.models import SiteConfiguration, User


USER_PASSWORD = 'password'


class UserFactory(django.DjangoModelFactory):
    class Meta:
        model = User

    username = Sequence(lambda n: 'user_%d' % n)
    password = PostGenerationMethodCall('set_password', USER_PASSWORD)
    first_name = Faker('first_name')
    last_name = Faker('last_name')
    full_name = Faker('name')
    email = Faker('safe_email')
    is_staff = False
    is_superuser = False
    is_active = True


class SiteFactory(django.DjangoModelFactory):
    class Meta:
        model = Site

    domain = Faker('domain_name')
    name = Faker('word')


class SiteConfigurationFactory(django.DjangoModelFactory):
    class Meta:
        model = SiteConfiguration

    site = SubFactory(SiteFactory)
    lms_url_root = Faker('url')
    catalog_api_url = Faker('url')
    platform_name = Faker('word')
    partner_from_address = Faker('safe_email')
    tos_url = Faker('url')
    privacy_policy_url = Faker('url')
    homepage_url = Faker('url')
    company_name = Faker('word')
    certificate_help_url = Faker('url')
    records_help_url = Faker('url')
    twitter_username = Faker('word')
