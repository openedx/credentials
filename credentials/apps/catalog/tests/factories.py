"""
Factories for tests of Credentials.
"""
import datetime
from uuid import uuid4

import factory
from factory.fuzzy import FuzzyDateTime, FuzzyText
from pytz import UTC

from credentials.apps.catalog.models import Course, CourseRun, Organization, Pathway, Program
from credentials.apps.core.tests.factories import SiteFactory


def add_m2m_data(m2m_relation, data):
    """ Helper function to enable factories to easily associate many-to-many data with created objects. """
    if data:
        m2m_relation.add(*data)


class OrganizationFactory(factory.DjangoModelFactory):
    class Meta(object):
        model = Organization

    site = factory.SubFactory(SiteFactory)
    uuid = factory.LazyFunction(uuid4)
    key = FuzzyText(prefix='course-id/')
    name = FuzzyText(prefix="Test Org ")


class CourseFactory(factory.DjangoModelFactory):
    class Meta(object):
        model = Course

    site = factory.SubFactory(SiteFactory)
    uuid = factory.LazyFunction(uuid4)
    key = FuzzyText(prefix='course-id/')
    title = FuzzyText(prefix="Test çօմɾʂҽ ")

    @factory.post_generation
    def owners(self, create, extracted):
        if create:
            add_m2m_data(self.owners, extracted)


class CourseRunFactory(factory.DjangoModelFactory):
    class Meta(object):
        model = CourseRun

    course = factory.SubFactory(CourseFactory)
    uuid = factory.LazyFunction(uuid4)
    key = FuzzyText(prefix='course-run-id/', suffix='/fake')
    title_override = None
    start_date = FuzzyDateTime(datetime.datetime(2014, 1, 1, tzinfo=UTC))
    end_date = FuzzyDateTime(datetime.datetime(2014, 1, 1, tzinfo=UTC)).end_dt


class ProgramFactory(factory.DjangoModelFactory):
    class Meta(object):
        model = Program

    site = factory.SubFactory(SiteFactory)
    uuid = factory.LazyFunction(uuid4)
    title = FuzzyText(prefix="Test Program ")
    type = FuzzyText()
    status = Program.ACTIVE

    @factory.post_generation
    def course_runs(self, create, extracted):
        if create:
            add_m2m_data(self.course_runs, extracted)

    @factory.post_generation
    def authoring_organizations(self, create, extracted):
        if create:
            add_m2m_data(self.authoring_organizations, extracted)


class PathwayFactory(factory.DjangoModelFactory):
    class Meta(object):
        model = Pathway

    uuid = factory.LazyFunction(uuid4)
    site = factory.SubFactory(SiteFactory)
    name = FuzzyText(prefix="Test Pathway ")
    org_name = FuzzyText()
    email = factory.Faker('safe_email')

    @factory.post_generation
    def programs(self, create, extracted):
        if create:
            add_m2m_data(self.programs, extracted)
