""" Tests for catalog utilities. """

from datetime import datetime

import ddt
from django.test import TestCase

from credentials.apps.catalog.models import Course, CourseRun, Organization, Program
from credentials.apps.catalog.tests.factories import CourseFactory
from credentials.apps.catalog.utils import (
    parse_course,
    parse_course_run,
    parse_organization,
    parse_pathway,
    parse_program,
)
from credentials.apps.core.tests.factories import SiteFactory
from credentials.shared.constants import PathwayType


@ddt.ddt
class ParseTests(TestCase):
    """ Course run tests. """
    ORG1_DATA = {'uuid': '33f0dded-fee9-4dec-a333-b9d8c2c82bd2', 'key': 'orgkey', 'name': 'Org Name'}
    ORG1_VALUES = ORG1_DATA

    COURSERUN1_DATA = {'uuid': '33f0dded-fee9-4dec-a333-b9d8c2c82bd3', 'key': 'runkey',
                       'title': 'Course Run Title',
                       'start_date': '2018-01-01T00:00:00Z', 'end_date': '2018-06-01T00:00:00Z'}
    COURSERUN1_VALUES = {'uuid': '33f0dded-fee9-4dec-a333-b9d8c2c82bd3', 'key': 'runkey',
                         'title_override': 'Course Run Title',
                         'start_date': datetime(2018, 1, 1), 'end_date': datetime(2018, 6, 1)}

    COURSE1_DATA = {'uuid': '33f0dded-fee9-4dec-a333-b9d8c2c82bd4', 'key': 'coursekey', 'title': 'Course Title',
                    'owners': [ORG1_DATA], 'course_runs': [COURSERUN1_DATA]}
    COURSE1_VALUES = {'uuid': '33f0dded-fee9-4dec-a333-b9d8c2c82bd4', 'key': 'coursekey', 'title': 'Course Title'}

    PROGRAM1_DATA = {'uuid': '33f0dded-fee9-4dec-a333-b9d8c2c82bd5', 'title': 'Program Title',
                     'authoring_organizations': [ORG1_DATA], 'courses': [COURSE1_DATA], 'type': 'MicroMasters',
                     'status': 'active', 'type_attrs': {'slug': 'micromasters'}}
    PROGRAM1_VALUES = {'uuid': '33f0dded-fee9-4dec-a333-b9d8c2c82bd5', 'title': 'Program Title',
                       'type': 'MicroMasters', 'status': 'active', 'type_slug': 'micromasters'}

    PATHWAY1_DATA = {'uuid': 'b13739e3-a966-4591-930e-a338e6083c63', 'name': 'Test Pathway', 'org_name': 'Pathway Org',
                     'email': 'test@example.com', 'programs': [PROGRAM1_DATA],
                     'pathway_type': PathwayType.INDUSTRY.value}  # Check type is industry since type defaults to credit

    def setUp(self):
        super().setUp()
        self.site = SiteFactory()

    @ddt.unpack
    @ddt.data(
        (ORG1_DATA, ORG1_VALUES, None),
        ({}, {}, KeyError),
    )
    def test_parse_organization(self, data, vals, err):
        """ Test parsing a single org. """
        if err:
            with self.assertRaises(err):
                parse_organization(self.site, data)
        else:
            org = parse_organization(self.site, data)
            self.assertEqual(Organization.objects.all().count(), 1)
            self.assertEqual(org, Organization.objects.get(site=self.site, **vals))

    @ddt.unpack
    @ddt.data(
        ('Course Run Title', COURSERUN1_DATA, dict(COURSERUN1_VALUES, title_override=None), None),
        ('Other Title', COURSERUN1_DATA, COURSERUN1_VALUES, None),
        ('', {}, {}, KeyError),
    )
    def test_parse_course_run(self, title, data, vals, err):
        """ Test parsing a single course run. """
        course = CourseFactory(title=title)
        if err:
            with self.assertRaises(err):
                parse_course_run(course, data)
        else:
            run = parse_course_run(course, data)
            self.assertEqual(CourseRun.objects.all().count(), 1)
            self.assertEqual(run, CourseRun.objects.get(course=course, **vals))

    @ddt.unpack
    @ddt.data(
        (COURSE1_DATA, COURSE1_VALUES, ['orgkey'], ['runkey'], None),
        ({}, {}, [], [], KeyError),
    )
    def test_parse_course(self, data, vals, org_keys_expected, run_keys_expected, err):
        """ Test parsing a single course with a course run. """
        if err:
            with self.assertRaises(err):
                parse_course(self.site, data)
        else:
            course, course_runs = parse_course(self.site, data)

            self.assertEqual(Course.objects.all().count(), 1)
            self.assertEqual(course, Course.objects.get(site=self.site, **vals))

            # Check runs
            run_keys = [c.key for c in course.course_runs.all()]
            self.assertListEqual(run_keys, run_keys_expected)
            self.assertEqual(CourseRun.objects.all().count(), len(run_keys))

            self.assertListEqual(list(course.course_runs.all()), course_runs)

            # Check orgs
            org_keys = [o.key for o in course.owners.all()]
            self.assertListEqual(org_keys, org_keys_expected)
            self.assertEqual(Organization.objects.all().count(), len(org_keys))

    def test_parse_course_atomic(self):
        """ Test that parsing a course is atomic. """

        data = dict(self.COURSE1_DATA)
        data.update(course_runs=[{}])

        with self.assertRaises(KeyError):
            parse_course(self.site, data)

        self.assertEqual(Course.objects.all().count(), 0)
        self.assertEqual(CourseRun.objects.all().count(), 0)
        self.assertEqual(Organization.objects.all().count(), 0)

    @ddt.unpack
    @ddt.data(
        (PROGRAM1_DATA, PROGRAM1_VALUES, ['orgkey'], ['runkey'], None),
        ({}, {}, [], [], KeyError),
    )
    def test_parse_program(self, data, vals, org_keys_expected, run_keys_expected, err):
        """ Test parsing a single program with one course/run. """
        if err:
            with self.assertRaises(err):
                parse_course(self.site, data)
        else:
            program = parse_program(self.site, data)

            self.assertEqual(Program.objects.all().count(), 1)
            self.assertEqual(program, Program.objects.get(site=self.site, **vals))

            # Check runs
            run_keys = [c.key for c in program.course_runs.all()]
            self.assertListEqual(run_keys, run_keys_expected)
            self.assertEqual(CourseRun.objects.all().count(), len(run_keys))

            # Check orgs
            org_keys = [o.key for o in program.authoring_organizations.all()]
            self.assertListEqual(org_keys, org_keys_expected)
            self.assertEqual(Organization.objects.all().count(), len(org_keys))

    def test_parse_program_atomic(self):
        """ Test that parsing a program is atomic. """

        data = dict(self.PROGRAM1_DATA)
        data.update(courses=[{}])

        with self.assertRaises(KeyError):
            parse_program(self.site, data)

        self.assertEqual(Program.objects.all().count(), 0)
        self.assertEqual(Course.objects.all().count(), 0)
        self.assertEqual(CourseRun.objects.all().count(), 0)
        self.assertEqual(Organization.objects.all().count(), 0)

    def test_parse_pathway(self):
        # We assume that programs are parsed separately from pathway data.
        parse_program(self.site, self.PROGRAM1_DATA)

        pathway = parse_pathway(self.site, self.PATHWAY1_DATA)
        assert pathway.uuid == self.PATHWAY1_DATA['uuid']
        assert pathway.name == self.PATHWAY1_DATA['name']
        assert pathway.email == self.PATHWAY1_DATA['email']
        assert pathway.org_name == self.PATHWAY1_DATA['org_name']
        assert str(pathway.programs.all()[0].uuid) == self.PROGRAM1_DATA['uuid']
        assert pathway.pathway_type == self.PATHWAY1_DATA['pathway_type']
