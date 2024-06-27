"""
Tests for the `api.py` file of the Records Django app.
"""

import datetime

from django.conf import settings
from django.contrib.contenttypes.models import ContentType
from django.template.defaultfilters import slugify
from django.test import TestCase
from edx_toggles.toggles.testutils import override_waffle_switch

from credentials.apps.catalog.tests.factories import (
    CourseFactory,
    CourseRunFactory,
    OrganizationFactory,
    PathwayFactory,
    ProgramFactory,
)
from credentials.apps.core.tests.factories import UserFactory
from credentials.apps.core.tests.mixins import SiteMixin
from credentials.apps.credentials.api import get_credential_dates
from credentials.apps.credentials.tests.factories import (
    CourseCertificateFactory,
    ProgramCertificateFactory,
    UserCredentialFactory,
)
from credentials.apps.records.api import (
    _does_awarded_program_cert_exist_for_user,
    _get_shared_program_cert_record_data,
    _get_transformed_grade_data,
    _get_transformed_learner_data,
    _get_transformed_pathway_data,
    _get_transformed_program_data,
)
from credentials.apps.records.constants import UserCreditPathwayStatus
from credentials.apps.records.tests.factories import (
    ProgramCertRecordFactory,
    UserCreditPathwayFactory,
    UserGradeFactory,
)


class ApiTests(SiteMixin, TestCase):
    """
    Tests for the utility functions of the Records Django app's `api.py` file.
    """

    def setUp(self):
        super().setUp()
        self.COURSE_CERTIFICATE_CONTENT_TYPE = ContentType.objects.get(
            app_label="credentials", model="coursecertificate"
        )
        self.PROGRAM_CERTIFICATE_CONTENT_TYPE = ContentType.objects.get(
            app_label="credentials", model="programcertificate"
        )
        # create the user to award the certificate(s) to
        self.user = UserFactory()
        # create the organization for the program
        self.org = OrganizationFactory.create(name="TestOrg1")
        # create three courses that we will use in our test cases
        self.course1 = CourseFactory.create(site=self.site)
        self.course2 = CourseFactory.create(site=self.site)
        self.course3 = CourseFactory.create(site=self.site)
        # create 2 course runs for course 1
        self.course1_courserunA = CourseRunFactory(course=self.course1)
        self.course1_courserunB = CourseRunFactory(course=self.course1)
        # create 1 course run for course 2
        self.course2_courserunA = CourseRunFactory(course=self.course2)
        # create 1 course run for course 3
        self.course3_courserunA = CourseRunFactory(course=self.course3)
        # create a list of the course runs in program1
        self.program1_course_runs = [self.course1_courserunA, self.course1_courserunB, self.course2_courserunA]
        self.program1 = ProgramFactory(
            title="Test Program 1",
            course_runs=self.program1_course_runs,
            authoring_organizations=[self.org],
            site=self.site,
        )
        # create a list of the course runs in program2
        self.program2_course_runs = [self.course1_courserunA, self.course3_courserunA]
        self.program2 = ProgramFactory(
            title="Test Program 2",
            course_runs=self.program2_course_runs,
            authoring_organizations=[self.org],
            site=self.site,
        )
        # create course certificate configurations so we can grant credentials to the test learner
        self.course_cert_course1_courserunA = CourseCertificateFactory(
            course_id=self.course1_courserunA.key, site=self.site
        )
        self.course_cert_course1_courserunB = CourseCertificateFactory(
            course_id=self.course1_courserunB.key, site=self.site
        )
        self.course_cert_course2_courserunA = CourseCertificateFactory(
            course_id=self.course2_courserunA.key, site=self.site
        )
        self.course_cert_course3_courserunA = CourseCertificateFactory(
            course_id=self.course3_courserunA.key, site=self.site
        )
        # create program certificate configurations so we can grant program credentials to the test learners
        self.program1_cert_config = ProgramCertificateFactory.create(
            program_uuid=self.program1.uuid, site=self.site, program=self.program1
        )
        self.program2_cert_config = ProgramCertificateFactory.create(
            program_uuid=self.program2.uuid, site=self.site, program=self.program2
        )
        # create grade for learner in course-run1 of course1
        self.course1_courserunA_grade = UserGradeFactory(
            username=self.user.username,
            course_run=self.course1_courserunA,
            letter_grade="C",
            percent_grade=0.75,
        )
        self.course1_courserunB_grade = UserGradeFactory(
            username=self.user.username,
            course_run=self.course1_courserunB,
            letter_grade="A",
            percent_grade=1.0,
        )
        self.course2_courserunA_grade = UserGradeFactory(
            username=self.user.username,
            course_run=self.course2_courserunA,
            letter_grade="B",
            percent_grade=0.85,
        )
        self.course3_courserunA_grade = UserGradeFactory(
            username=self.user.username, course_run=self.course3_courserunA, letter_grade="A", percent_grade=0.91
        )
        # next, award the course and program credentials to our test learner
        self.course_credential_course1_courserunA = UserCredentialFactory.create(
            username=self.user.username,
            credential_content_type=self.COURSE_CERTIFICATE_CONTENT_TYPE,
            credential=self.course_cert_course1_courserunA,
        )
        self.course_credential_course1_courserunB = UserCredentialFactory.create(
            username=self.user.username,
            credential_content_type=self.COURSE_CERTIFICATE_CONTENT_TYPE,
            credential=self.course_cert_course1_courserunB,
        )
        self.course_credential_course2_courserunA = UserCredentialFactory.create(
            username=self.user.username,
            credential_content_type=self.COURSE_CERTIFICATE_CONTENT_TYPE,
            credential=self.course_cert_course2_courserunA,
        )
        self.course_credential_course3_courserunA = UserCredentialFactory.create(
            username=self.user.username,
            credential_content_type=self.COURSE_CERTIFICATE_CONTENT_TYPE,
            credential=self.course_cert_course3_courserunA,
        )
        self.program_credential = UserCredentialFactory.create(
            username=self.user.username,
            credential_content_type=self.PROGRAM_CERTIFICATE_CONTENT_TYPE,
            credential=self.program1_cert_config,
        )
        # setup a credit pathway and then add a pathway record for our user
        self.pathway = PathwayFactory(site=self.site, programs=[self.program1])
        UserCreditPathwayFactory(user=self.user, pathway=self.pathway, status=UserCreditPathwayStatus.SENT)
        # create a shared program cert record for our user
        self.shared_program_cert_record = ProgramCertRecordFactory(
            uuid=self.program1.uuid, program=self.program1, user=self.user
        )

    def _assert_results(self, expected_result, result):
        """
        Utility function that compares two dictionaries and verifies the results generated by our code matches the
        expected results.
        """
        expected_keys = expected_result.keys()
        for key in expected_keys:
            assert result[key] == expected_result[key]

    def test_does_awarded_program_cert_exist_for_user_with_cert(self):
        """
        Test that verifies the functionality of the `_does_awarded_program_cert_exist_for_user` utility function when a
        certificate exists for the user.
        """
        result = _does_awarded_program_cert_exist_for_user(self.program1, self.user)
        assert result is True

    def test_does_awarded_program_cert_exist_for_user_no_cert(self):
        """
        Test that verifies the functionality of the `_does_awarded_program_cert_exist_for_user` utility function when a
        certificate exists for the user.
        """
        self.program_credential.revoke()

        result = _does_awarded_program_cert_exist_for_user(self.program1, self.user)
        assert result is False

    def test_get_transformed_learner_data(self):
        """
        Test that verifies the functionality of the `_get_transformed_learner_data` utility function.
        """
        expected_result = {
            "full_name": self.user.get_full_name(),
            "username": self.user.username,
            "email": self.user.email,
        }

        result = _get_transformed_learner_data(self.user)
        self._assert_results(expected_result, result)

    def test_get_transformed_program_data(self):
        """
        Test that verifies the functionality of the `_get_transformed_program_data` utiltiy function.
        """
        last_updated = datetime.datetime.now()

        expected_result = {
            "name": self.program1.title,
            "type": slugify(self.program1.type),
            "type_name": self.program1.type,
            "completed": True,
            "empty": True,
            "last_updated": last_updated.isoformat(),
            "school": ", ".join(self.program1.authoring_organizations.values_list("name", flat=True)),
        }

        result = _get_transformed_program_data(self.program1, self.user, {}, last_updated)
        self._assert_results(expected_result, result)

    def test_get_transformed_pathway_data(self):
        """
        Test that verifies the functionality of the `_get_transformed_pathway_data` utility function.
        """
        expected_result = {
            "name": self.pathway.name,
            "id": self.pathway.id,
            "status": UserCreditPathwayStatus.SENT,
            "is_active": True,
            "pathway_type": self.pathway.pathway_type,
        }

        result = _get_transformed_pathway_data(self.program1, self.user)
        self._assert_results(expected_result, result[0])

    def test_get_transformed_grade_data(self):
        """
        Test that verifies the functionality of the `_get_transformed_grade_data` utility function. In this scenario we
        have one program associated with two courses, across three course runs. The test verifies that the grade and
        dates associated with the learner's achievements are what we would expect.
        """
        expected_issue_date_course1 = get_credential_dates(self.course_credential_course1_courserunB, False)
        expected_issue_date_course2 = get_credential_dates(self.course_credential_course2_courserunA, False)
        expected_result = [
            {
                "name": self.course1.title,
                "school": ",".join(self.course1.owners.values_list("name", flat=True)),
                "attempts": 2,
                "course_id": self.course1_courserunB.key,
                "issue_date": expected_issue_date_course1.isoformat(),
                "percent_grade": 1.0,
                "letter_grade": "A",
            },
            {
                "name": self.course2.title,
                "school": ",".join(self.course2.owners.values_list("name", flat=True)),
                "attempts": 1,
                "course_id": self.course2_courserunA.key,
                "issue_date": expected_issue_date_course2.isoformat(),
                "percent_grade": 0.85,
                "letter_grade": "B",
            },
        ]
        expected_highest_attempt_dict = {
            self.course1: self.course1_courserunB_grade,
            self.course2: self.course2_courserunA_grade,
        }

        result, highest_attempt_dict, last_updated = _get_transformed_grade_data(self.program1, self.user)
        self._assert_results(expected_result[0], result[0])
        self._assert_results(expected_result[1], result[1])
        self._assert_results(expected_highest_attempt_dict, highest_attempt_dict)
        assert expected_issue_date_course2 == last_updated

    def test_get_transformed_grade_data_has_credential_missing_grade(self):
        """
        A test that verifies an edge case of the `_get_transformed_data_data` utility function. If the learner has
        earned a course credential in a course, but there is no grade information available, we should still populate
        some data about the credential in the returned data. This is import so that the Learner Record MFE can
        accurately render data about the learner's achievements in their programs.
        """
        # delete the grade record for the learner in "course2"
        self.course2_courserunA_grade.delete()

        expected_issue_date_course1 = get_credential_dates(self.course_credential_course1_courserunB, False)
        expected_issue_date_course2 = get_credential_dates(self.course_credential_course2_courserunA, False)
        expected_result = [
            {
                "name": self.course1.title,
                "school": ",".join(self.course1.owners.values_list("name", flat=True)),
                "attempts": 2,
                "course_id": self.course1_courserunB.key,
                "issue_date": expected_issue_date_course1.isoformat(),
                "percent_grade": 1.0,
                "letter_grade": "A",
            },
            {
                "name": self.course2.title,
                "school": ",".join(self.course2.owners.values_list("name", flat=True)),
                "attempts": "",
                "course_id": self.course2_courserunA.key,
                "issue_date": expected_issue_date_course2.isoformat(),
                "percent_grade": "",
                "letter_grade": "",
            },
        ]
        expected_highest_attempt_dict = {
            self.course1: self.course1_courserunB_grade,
        }

        result, highest_attempt_dict, last_updated = _get_transformed_grade_data(self.program1, self.user)
        self._assert_results(expected_result[0], result[0])
        self._assert_results(expected_result[1], result[1])
        self._assert_results(expected_highest_attempt_dict, highest_attempt_dict)
        # in this case, because of how the logic currently is implemented, we should expect the "last updated" date to
        # be associated with available grades
        assert expected_issue_date_course1 == last_updated

    def test_get_transformed_grade_data_no_progress(self):
        """
        A test that verifies an edge case of the `_get_transformed_grade_data` utility function. If the learner has made
        no progress in any course of a program, we should return expect data sets.
        """
        # "remove" progress in the learner's courses by deleting our credential and grade records
        self.course_credential_course1_courserunA.delete()
        self.course_credential_course1_courserunB.delete()
        self.course_credential_course2_courserunA.delete()
        self.course_credential_course3_courserunA.delete()
        self.course1_courserunA_grade.delete()
        self.course1_courserunB_grade.delete()
        self.course2_courserunA_grade.delete()
        self.course3_courserunA_grade.delete()

        expected_result = [
            {
                "name": self.course1.title,
                "school": ",".join(self.course1.owners.values_list("name", flat=True)),
                "attempts": "",
                "course_id": "",
                "issue_date": "",
                "percent_grade": "",
                "letter_grade": "",
            },
            {
                "name": self.course2.title,
                "school": ",".join(self.course2.owners.values_list("name", flat=True)),
                "attempts": "",
                "course_id": "",
                "issue_date": "",
                "percent_grade": "",
                "letter_grade": "",
            },
        ]

        result, highest_attempt_dict, _ = _get_transformed_grade_data(self.program1, self.user)
        self._assert_results(expected_result[0], result[0])
        self._assert_results(expected_result[1], result[1])
        self._assert_results({}, highest_attempt_dict)

    def test_get_transformed_grade_data_no_grade_no_credential(self):
        """
        A test that verifies an edge case of the `_get_transformed_grade_data` utility function. If there is no grade
        nor a credential associated with a learner in a course/course-run of a program, we should include a default
        result with mostly empty fields.
        """
        # delete grade and course credential for learner in "course2"
        self.course2_courserunA_grade.delete()
        self.course_credential_course2_courserunA.delete()

        expected_issue_date_course1 = get_credential_dates(self.course_credential_course1_courserunB, False)
        expected_result = [
            {
                "name": self.course1.title,
                "school": ",".join(self.course1.owners.values_list("name", flat=True)),
                "attempts": 2,
                "course_id": self.course1_courserunB.key,
                "issue_date": expected_issue_date_course1.isoformat(),
                "percent_grade": 1.0,
                "letter_grade": "A",
            },
            {
                "name": self.course2.title,
                "school": ",".join(self.course2.owners.values_list("name", flat=True)),
                "attempts": "",
                "course_id": "",
                "issue_date": "",
                "percent_grade": "",
                "letter_grade": "",
            },
        ]
        expected_highest_attempt_dict = {
            self.course1: self.course1_courserunB_grade,
        }

        result, highest_attempt_dict, last_updated = _get_transformed_grade_data(self.program1, self.user)
        self._assert_results(expected_result[0], result[0])
        self._assert_results(expected_result[1], result[1])
        self._assert_results(expected_highest_attempt_dict, highest_attempt_dict)
        assert expected_issue_date_course1 == last_updated

    @override_waffle_switch(settings.USE_CERTIFICATE_AVAILABLE_DATE, active=True)
    def test_get_transformed_grade_data_earned_credential_with_certificate_available_date(self):
        """
        A test that verifies an edge case of the `_get_transformed_grade_data` utility function. If a course credential
        is associated with a certificate availability date that is set in the future, then it should not be included as
        part of the results. In this test scenario, we add a certificate available date to the course certificate
        associated with the "course1_courserun2" course run and then verify the data that is returned by the function.
        """
        self.course_cert_course1_courserunB.certificate_available_date = "9999-05-11T03:14:01Z"
        self.course_cert_course1_courserunB.save()

        expected_issue_date_course1 = get_credential_dates(self.course_credential_course1_courserunA, False)
        expected_issue_date_course2 = get_credential_dates(self.course_credential_course2_courserunA, False)
        expected_result = [
            {
                "name": self.course1.title,
                "school": ",".join(self.course1.owners.values_list("name", flat=True)),
                "attempts": 1,
                "course_id": self.course1_courserunA.key,
                "issue_date": expected_issue_date_course1.isoformat(),
                "percent_grade": 0.75,
                "letter_grade": "C",
            },
            {
                "name": self.course2.title,
                "school": ",".join(self.course2.owners.values_list("name", flat=True)),
                "attempts": 1,
                "course_id": self.course2_courserunA.key,
                "issue_date": expected_issue_date_course2.isoformat(),
                "percent_grade": 0.85,
                "letter_grade": "B",
            },
        ]
        expected_highest_attempt_dict = {
            self.course1: self.course1_courserunA_grade,
            self.course2: self.course2_courserunA_grade,
        }

        result, highest_attempt_dict, last_updated = _get_transformed_grade_data(self.program1, self.user)
        self._assert_results(expected_result[0], result[0])
        self._assert_results(expected_result[1], result[1])
        self._assert_results(expected_highest_attempt_dict, highest_attempt_dict)
        assert expected_issue_date_course2 == last_updated

    def test_get_transformed_grade_data_program_with_excluded_course_run(self):
        """
        A test that verifies an edge case of the `_get_transformed_grade_data` utility function. It is possible for two
        unique programs to share a subset of courses and course runs between them. The Discovery service allows us to
        explicitly exclude specific course runs from a program.

        This test ensures the functionality of the data presented in the Learner Record MFE, verifying that we don't
        display course data to a learner if a course run has been explicitly excluded from a program.
        """
        expected_issue_date_course1_courserun1 = get_credential_dates(self.course_credential_course1_courserunA, False)
        expected_issue_date_course1_courserun2 = get_credential_dates(self.course_credential_course1_courserunB, False)
        expected_issue_date_course2 = get_credential_dates(self.course_credential_course2_courserunA, False)
        expected_issue_date_course3 = get_credential_dates(self.course_credential_course3_courserunA, False)
        expected_results_program1 = [
            {
                "name": self.course1.title,
                "school": ",".join(self.course1.owners.values_list("name", flat=True)),
                "attempts": 2,
                "course_id": self.course1_courserunB.key,
                "issue_date": expected_issue_date_course1_courserun2.isoformat(),
                "percent_grade": 1.0,
                "letter_grade": "A",
            },
            {
                "name": self.course2.title,
                "school": ",".join(self.course2.owners.values_list("name", flat=True)),
                "attempts": 1,
                "course_id": self.course2_courserunA.key,
                "issue_date": expected_issue_date_course2.isoformat(),
                "percent_grade": 0.85,
                "letter_grade": "B",
            },
        ]
        expected_results_program2 = [
            {
                "name": self.course1.title,
                "school": ",".join(self.course1.owners.values_list("name", flat=True)),
                "attempts": 1,
                "course_id": self.course1_courserunA.key,
                "issue_date": expected_issue_date_course1_courserun1.isoformat(),
                "percent_grade": 0.75,
                "letter_grade": "C",
            },
            {
                "name": self.course3.title,
                "school": ",".join(self.course3.owners.values_list("name", flat=True)),
                "attempts": 1,
                "course_id": self.course3_courserunA.key,
                "issue_date": expected_issue_date_course3.isoformat(),
                "percent_grade": 0.91,
                "letter_grade": "A",
            },
        ]
        expected_highest_attempt_dict_program1 = {
            self.course1: self.course1_courserunB_grade,
            self.course2: self.course2_courserunA_grade,
        }
        expected_highest_attempt_dict_program2 = {
            self.course1: self.course1_courserunA_grade,
            self.course3: self.course3_courserunA_grade,
        }

        result_prog1, highest_attempt_dict_prog1, last_updated_prog1 = _get_transformed_grade_data(
            self.program1, self.user
        )
        result_prog2, highest_attempt_dict_prog2, last_updated_prog2 = _get_transformed_grade_data(
            self.program2, self.user
        )
        # verify results of "program1"
        self._assert_results(expected_results_program1[0], result_prog1[0])
        self._assert_results(expected_results_program1[1], result_prog1[1])
        self._assert_results(expected_highest_attempt_dict_program1, highest_attempt_dict_prog1)
        assert expected_issue_date_course2 == last_updated_prog1
        # verify results of "program2"
        self._assert_results(expected_results_program2[0], result_prog2[0])
        self._assert_results(expected_results_program2[1], result_prog2[1])
        self._assert_results(expected_highest_attempt_dict_program2, highest_attempt_dict_prog2)
        assert expected_issue_date_course3 == last_updated_prog2

    def test_get_transformed_grade_data_program_with_excluded_course_run_no_grade(self):
        """
        A test that verifies an edge case of the `_get_transformed_grade_data` utility function. It is possible for two
        unique programs to share a subset of courses and course runs between them. The Discovery service allows us to
        explicitly exclude specific course runs from a program.

        This test ensures the functionality of the data presented in the Learner Record MFE, verifying that we don't
        display course data to a learner if a course run has been explicitly excluded from a program.

        This is an additional edge case to the previous unit test where grade data is missing, but we still want to
        ensure the (course) credential data is returned.
        """
        self.course3_courserunA_grade.delete()

        expected_issue_date_course1_courserun1 = get_credential_dates(self.course_credential_course1_courserunA, False)
        expected_issue_date_course1_courserun2 = get_credential_dates(self.course_credential_course1_courserunB, False)
        expected_issue_date_course2 = get_credential_dates(self.course_credential_course2_courserunA, False)
        expected_issue_date_course3 = get_credential_dates(self.course_credential_course3_courserunA, False)
        expected_results_program1 = [
            {
                "name": self.course1.title,
                "school": ",".join(self.course1.owners.values_list("name", flat=True)),
                "attempts": 2,
                "course_id": self.course1_courserunB.key,
                "issue_date": expected_issue_date_course1_courserun2.isoformat(),
                "percent_grade": 1.0,
                "letter_grade": "A",
            },
            {
                "name": self.course2.title,
                "school": ",".join(self.course2.owners.values_list("name", flat=True)),
                "attempts": 1,
                "course_id": self.course2_courserunA.key,
                "issue_date": expected_issue_date_course2.isoformat(),
                "percent_grade": 0.85,
                "letter_grade": "B",
            },
        ]
        expected_results_program2 = [
            {
                "name": self.course1.title,
                "school": ",".join(self.course1.owners.values_list("name", flat=True)),
                "attempts": 1,
                "course_id": self.course1_courserunA.key,
                "issue_date": expected_issue_date_course1_courserun1.isoformat(),
                "percent_grade": 0.75,
                "letter_grade": "C",
            },
            {
                "name": self.course3.title,
                "school": ",".join(self.course3.owners.values_list("name", flat=True)),
                "attempts": "",
                "course_id": self.course3_courserunA.key,
                "issue_date": expected_issue_date_course3.isoformat(),
                "percent_grade": "",
                "letter_grade": "",
            },
        ]
        expected_highest_attempt_dict_program1 = {
            self.course1: self.course1_courserunB_grade,
            self.course2: self.course2_courserunA_grade,
        }
        expected_highest_attempt_dict_program2 = {
            self.course1: self.course1_courserunA_grade,
        }

        result_prog1, highest_attempt_dict_prog1, last_updated_prog1 = _get_transformed_grade_data(
            self.program1, self.user
        )
        result_prog2, highest_attempt_dict_prog2, last_updated_prog2 = _get_transformed_grade_data(
            self.program2, self.user
        )
        # verify results of "program1"
        self._assert_results(expected_results_program1[0], result_prog1[0])
        self._assert_results(expected_results_program1[1], result_prog1[1])
        self._assert_results(expected_highest_attempt_dict_program1, highest_attempt_dict_prog1)
        assert expected_issue_date_course2 == last_updated_prog1
        # verify results of "program2"
        self._assert_results(expected_results_program2[0], result_prog2[0])
        self._assert_results(expected_results_program2[1], result_prog2[1])
        self._assert_results(expected_highest_attempt_dict_program2, highest_attempt_dict_prog2)
        assert expected_issue_date_course1_courserun1 == last_updated_prog2

    def test_get_shared_program_cert_record_data(self):
        """
        Test that verifies the functionality of the `_get_shared_program_cert_record_data` utility function.
        """
        result = _get_shared_program_cert_record_data(self.program1, self.user)
        assert result == str(self.shared_program_cert_record.uuid.hex)

    def test_get_shared_program_cert_record_data_record_dne(self):
        """
        Test that verifies the functionality of the `_get_shared_program_cert_record_data` utility function when a
        shared record does not exist.
        """
        self.shared_program_cert_record.delete()

        result = _get_shared_program_cert_record_data(self.program1, self.user)
        assert result is None
