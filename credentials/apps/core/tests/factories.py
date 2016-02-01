"""
Factories for tests of Credentials.
"""
import factory

from credentials.apps.core.models import SiteConfiguration, User


class UserFactory(factory.django.DjangoModelFactory):  # pylint: disable=missing-docstring
    class Meta(object):  # pylint: disable=missing-docstring
        model = User

    username = factory.Sequence(lambda n: 'test-user-{}'.format(n))  # pylint: disable=unnecessary-lambda
    first_name = "dummy"
    last_name = "dummy"
    email = "dummy@example.com"
    is_staff = False
    is_active = True


class SiteConfigurationFactory(factory.django.DjangoModelFactory):  # pylint: disable=missing-docstring
    class Meta(object):  # pylint: disable=missing-docstring
        model = SiteConfiguration
