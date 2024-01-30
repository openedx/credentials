"""
Factories for tests of Credentials.
"""

import datetime
from uuid import uuid4

import factory
from factory.fuzzy import FuzzyDateTime, FuzzyInteger, FuzzyText
from pytz import UTC
from slugify import slugify

from credentials.apps.catalog.models import Course, CourseRun, Organization, Pathway, Program
from credentials.apps.core.tests.factories import SiteFactory


def add_m2m_data(m2m_relation, data):
    """Helper function to enable factories to easily associate many-to-many data with created objects."""
    if data:
        m2m_relation.add(*data)


class OrganizationFactory(factory.django.DjangoModelFactory):
    class Meta:
        model = Organization

    site = factory.SubFactory(SiteFactory)
    uuid = factory.LazyFunction(uuid4)
    key = FuzzyText(prefix="course-id/")
    name = FuzzyText(prefix="Test Org ")
    certificate_logo_image_url = FuzzyText(prefix="http://", suffix=".com/image.jpg")


class CourseFactory(factory.django.DjangoModelFactory):
    class Meta:
        model = Course

    site = factory.SubFactory(SiteFactory)
    uuid = factory.LazyFunction(uuid4)
    key = FuzzyText(prefix="course-id/")
    title = FuzzyText(prefix="Test çօմɾʂҽ ")

    @factory.post_generation
    def owners(self, create, extracted):
        if create:
            add_m2m_data(self.owners, extracted)


class CourseRunFactory(factory.django.DjangoModelFactory):
    class Meta:
        model = CourseRun

    course = factory.SubFactory(CourseFactory)
    uuid = factory.LazyFunction(uuid4)
    key = FuzzyText(prefix="course-run-id/", suffix="/fake")
    title_override = None
    start_date = FuzzyDateTime(datetime.datetime(2014, 1, 1, tzinfo=UTC))
    end_date = FuzzyDateTime(datetime.datetime(2014, 1, 1, tzinfo=UTC)).end_dt


class ProgramFactory(factory.django.DjangoModelFactory):
    class Meta:
        model = Program

    site = factory.SubFactory(SiteFactory)
    uuid = factory.LazyFunction(uuid4)
    title = FuzzyText(prefix="Test Program ")
    type = FuzzyText()
    type_slug = factory.LazyAttribute(lambda o: slugify(o.type))
    status = Program.ACTIVE
    total_hours_of_effort = FuzzyInteger(0)

    @factory.post_generation
    def course_runs(self, create, extracted):
        if create:
            add_m2m_data(self.course_runs, extracted)

    @factory.post_generation
    def authoring_organizations(self, create, extracted):
        if create:
            add_m2m_data(self.authoring_organizations, extracted)


class PathwayFactory(factory.django.DjangoModelFactory):
    class Meta:
        model = Pathway

    uuid = factory.LazyFunction(uuid4)
    site = factory.SubFactory(SiteFactory)
    name = FuzzyText(prefix="Test Pathway ")
    org_name = FuzzyText()
    email = factory.Faker("safe_email")

    @factory.post_generation
    def programs(self, create, extracted):
        if create:
            add_m2m_data(self.programs, extracted)
