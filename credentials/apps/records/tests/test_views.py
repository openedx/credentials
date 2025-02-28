"""
Tests for records rendering views.
"""

import csv
import io
import json
import re
import urllib.parse
from unittest.mock import patch

import ddt
from django.conf import settings
from django.contrib.contenttypes.models import ContentType
from django.core import mail
from django.test import TestCase
from django.test.utils import override_settings
from django.urls import reverse

from credentials.apps.catalog.data import PathwayStatus
from credentials.apps.catalog.tests.factories import (
    CourseFactory,
    CourseRunFactory,
    OrganizationFactory,
    PathwayFactory,
    ProgramFactory,
)
from credentials.apps.core.tests.factories import USER_PASSWORD, UserFactory
from credentials.apps.core.tests.mixins import SiteMixin
from credentials.apps.credentials.constants import UUID_PATTERN
from credentials.apps.credentials.models import UserCredential
from credentials.apps.credentials.tests.factories import (
    CourseCertificateFactory,
    ProgramCertificateFactory,
    UserCredentialFactory,
)
from credentials.apps.records.constants import UserCreditPathwayStatus
from credentials.apps.records.models import ProgramCertRecord, UserCreditPathway
from credentials.apps.records.tests.factories import (
    ProgramCertRecordFactory,
    UserCreditPathwayFactory,
    UserGradeFactory,
)
from credentials.apps.records.tests.utils import dump_random_state


JSON_CONTENT_TYPE = "application/json"


class ProgramRecordTests(SiteMixin, TestCase):
    USERNAME = "test-user"

    def setUp(self):
        super().setUp()
        dump_random_state()

        user = UserFactory(username=self.USERNAME)
        self.client.login(username=user.username, password=USER_PASSWORD)
        self.program = ProgramFactory(site=self.site)

    def test_login_required(self):
        """Verify no access without a login"""
        self.client.logout()
        rev = reverse("records:share_program", kwargs={"uuid": self.program.uuid.hex})
        data = {"username": self.USERNAME}
        response = self.client.post(rev, data)
        self.assertEqual(response.status_code, 302)  # redirect to a login page
        self.assertTrue(response.url.startswith("/login/?next="))

    def test_user_creation(self):
        """Verify successful creation of a ProgramCertRecord and return of a URL with the uuid for the public record"""
        rev = reverse("records:share_program", kwargs={"uuid": self.program.uuid.hex})
        data = {"username": self.USERNAME}
        jdata = json.dumps(data).encode("utf-8")
        response = self.client.post(rev, data=jdata, content_type=JSON_CONTENT_TYPE)
        json_data = response.json()

        self.assertEqual(response.status_code, 201)
        self.assertRegex(json_data["url"], UUID_PATTERN)

    def test_different_user_creation(self):
        """Verify that the view rejects a User attempting to create a ProgramCertRecord for another"""
        diff_username = "diff-user"
        rev = reverse("records:share_program", kwargs={"uuid": self.program.uuid.hex})
        UserFactory(username=diff_username)
        data = {"username": diff_username}
        jdata = json.dumps(data).encode("utf-8")
        response = self.client.post(rev, data=jdata, content_type=JSON_CONTENT_TYPE)

        self.assertEqual(response.status_code, 403)

    def test_pcr_already_exists(self):
        """Verify that the view returns the existing ProgramCertRecord when one already exists for the given username
        and program certificate uuid"""
        rev = reverse("records:share_program", kwargs={"uuid": self.program.uuid.hex})
        data = {"username": self.USERNAME}
        jdata = json.dumps(data).encode("utf-8")
        response = self.client.post(rev, data=jdata, content_type=JSON_CONTENT_TYPE)
        url1 = response.json()["url"]
        self.assertEqual(response.status_code, 201)

        response = self.client.post(rev, data=jdata, content_type=JSON_CONTENT_TYPE)
        url2 = response.json()["url"]
        self.assertEqual(response.status_code, 200)

        self.assertEqual(url1, url2)


@ddt.ddt
@override_settings(EMAIL_BACKEND="django.core.mail.backends.locmem.EmailBackend")
class ProgramSendTests(SiteMixin, TestCase):
    USERNAME = "test-user"

    def setUp(self):
        super().setUp()

        self.user = UserFactory(username=self.USERNAME)
        self.client.login(username=self.user.username, password=USER_PASSWORD)
        self.program = ProgramFactory(site=self.site)
        self.pathway = PathwayFactory(site=self.site, programs=[self.program])
        self.pc = ProgramCertificateFactory(site=self.site, program_uuid=self.program.uuid)
        self.user_credential = UserCredentialFactory(username=self.USERNAME, credential=self.pc)
        self.data = {"username": self.USERNAME, "pathway_id": self.pathway.id}
        self.url = reverse("records:send_program", kwargs={"uuid": self.program.uuid.hex})

        mail.outbox = []

    def post(self):
        jdata = json.dumps(self.data).encode("utf-8")
        return self.client.post(self.url, data=jdata, content_type=JSON_CONTENT_TYPE)

    def test_login_required(self):
        """Verify no access without a login"""
        self.client.logout()
        response = self.post()
        self.assertEqual(response.status_code, 302)  # redirect to a login page
        self.assertTrue(response.url.startswith("/login/?next="))

    def test_creates_cert_record(self):
        """Verify that the view creates a ProgramCertRecord as needed."""
        with self.assertRaises(ProgramCertRecord.DoesNotExist):
            ProgramCertRecord.objects.get(user=self.user, program=self.program)

        response = self.post()
        self.assertEqual(response.status_code, 200)

        ProgramCertRecord.objects.get(user=self.user, program=self.program)

    def test_different_user(self):
        """Verify that the view rejects a User attempting to send a program"""
        diff_username = "diff-user"
        UserFactory(username=diff_username)
        self.data["username"] = diff_username

        response = self.post()
        self.assertEqual(response.status_code, 403)

    @patch("credentials.apps.records.views.ace")
    def test_from_address_set(self, mock_ace):
        """Verify that the email uses the proper from address"""
        response = self.post()
        self.assertEqual(response.status_code, 200)
        self.assertEqual(
            mock_ace.send.call_args[0][0].options["from_address"], self.site_configuration.partner_from_address
        )

    @patch("credentials.apps.records.views.ace")
    def test_no_full_name(self, mock_ace):
        """Verify that the email uses the username as a backup for the full name."""
        self.user.full_name = ""
        self.user.first_name = ""
        self.user.last_name = ""
        self.user.save()

        response = self.post()
        self.assertEqual(response.status_code, 200)
        self.assertEqual(mock_ace.send.call_args[0][0].context["user_full_name"], self.user.username)

    @patch("credentials.apps.records.views.ace")
    def test_from_address_unset(self, mock_ace):
        """Verify that the email uses the proper default from address"""
        self.site_configuration.partner_from_address = None
        self.site_configuration.save()

        response = self.post()
        self.assertEqual(response.status_code, 200)
        self.assertEqual(mock_ace.send.call_args[0][0].options["from_address"], "no-reply@" + self.site.domain)

    def test_email_content_complete(self):
        """Verify an email is actually sent"""
        response = self.post()
        self.assertEqual(response.status_code, 200)
        public_record = ProgramCertRecord.objects.get(user=self.user, program=self.program)
        record_path = reverse("records:public_programs", kwargs={"uuid": public_record.uuid.hex})
        record_link = "http://" + self.site.domain + record_path
        csv_link = urllib.parse.urljoin(record_link, "csv")

        # Check output and make sure it seems correct
        self.assertEqual(len(mail.outbox), 1)
        email = mail.outbox[0]
        message = str(email.message())
        self.assertIn(self.program.title + " Credit Request for", email.subject)
        self.assertIn(
            self.user.get_full_name() + " would like to apply for credit in the " + self.pathway.name, message
        )
        self.assertIn("has sent their completed program record for", message)
        self.assertIn('<a href="' + record_link + '">View Program Record</a>', message)
        self.assertIn('<a href="' + csv_link + '">Download Record (CSV)</a>', message)
        self.assertEqual(self.site_configuration.partner_from_address, email.from_email)
        self.assertEqual(self.user.email, email.reply_to[0])
        self.assertListEqual([self.pathway.email], email.to)

    @ddt.data(
        (PathwayStatus.PUBLISHED.value, 200),
        (PathwayStatus.UNPUBLISHED.value, 404),
        (PathwayStatus.RETIRED.value, 404),
    )
    @ddt.unpack
    def test_pathway_must_be_published(self, pathway_status, http_status):
        """Verify a pathway only sends if its status is published or empty"""
        self.pathway.status = pathway_status
        self.pathway.save()
        response = self.post()
        self.assertEqual(response.status_code, http_status)

    def test_email_content_incomplete(self):
        """Verify an email is actually sent"""
        self.user_credential.delete()
        response = self.post()
        self.assertEqual(response.status_code, 200)

        # Check output and make sure it seems correct
        self.assertEqual(len(mail.outbox), 1)
        email = mail.outbox[0]
        self.assertIn("has sent their partially completed program record for", str(email.message()))

    def test_allowed_sending_second_email(self):
        """Verify that an email can be sent more than once"""
        UserCreditPathwayFactory(pathway=self.pathway, user=self.user)
        response = self.post()
        self.assertEqual(response.status_code, 200)

    def test_resend_email(self):
        """Verify that a manually updated email status can be resent"""
        UserCreditPathwayFactory(pathway=self.pathway, user=self.user, program=self.program, status="")
        response = self.post()
        self.assertEqual(response.status_code, 200)
        user_credit_pathway = UserCreditPathway.objects.get(user=self.user, pathway=self.pathway, program=self.program)
        self.assertEqual(user_credit_pathway.status, UserCreditPathwayStatus.SENT)

    def test_resend_with_program(self):
        """verify that updating with a program updates a previous record with no program"""

        # create the artifacts left after a legacy call to send record
        ProgramCertRecordFactory(user=self.user, program=self.program, uuid=self.program.uuid)
        UserCreditPathwayFactory(pathway=self.pathway, user=self.user, program=None, status="")

        response = self.post()
        self.assertEqual(response.status_code, 200, "Invalid response from post")

        # If there are more than one, it means it was not updated, but a new user credit pathway created
        pathwayCount = UserCreditPathway.objects.filter(pathway=self.pathway, user=self.user).count()
        self.assertEqual(pathwayCount, 1, "Pathway was not updated")
        refetched_ucp = UserCreditPathway.objects.get(user=self.user, pathway=self.pathway)
        self.assertEqual(refetched_ucp.program, self.program, "Incorrect program associated with Pathway")

    def test_send_with_new_program(self):
        """Verify that an existing user credit pathway with no program is not
        modified when a new one is created with a new program"""
        legacyProgram = ProgramFactory(title="testProgram2")
        ProgramCertRecordFactory(user=self.user, program=legacyProgram, uuid=legacyProgram.uuid)
        UserCreditPathwayFactory(pathway=self.pathway, user=self.user, program=None, status="")
        response = self.post()
        # there should now be two
        self.assertEqual(
            UserCreditPathway.objects.filter(pathway=self.pathway, user=self.user).count(),
            2,
            "Did not find expected number of UserCreditPathway items.",
        )

        self.assertEqual(
            UserCreditPathway.objects.filter(pathway=self.pathway, user=self.user, program=None).count(),
            1,
            "UserCreditPathway with null progam incorrectly updated",
        )

        self.assertEqual(
            UserCreditPathway.objects.filter(pathway=self.pathway, user=self.user, program=self.program).count(),
            1,
            "New UserCreditPathway not created when null program UserCreditPathway exists",
        )

        response = self.post()
        self.assertEqual(response.status_code, 200)


@ddt.ddt
class ProgramRecordCsvViewTests(SiteMixin, TestCase):
    MOCK_USER_DATA = {
        "username": "test-user",
        "name": "Test User",
        "email": "test@example.org",
    }

    def setUp(self):
        super().setUp()
        self.user = UserFactory(username=self.MOCK_USER_DATA["username"])
        self.course = CourseFactory(site=self.site)
        self.course_runs = [CourseRunFactory(course=self.course) for _ in range(3)]
        self.user_grade_low = UserGradeFactory(
            username=self.MOCK_USER_DATA["username"],
            course_run=self.course_runs[0],
            letter_grade="A",
            percent_grade=0.70,
        )
        self.user_grade_high = UserGradeFactory(
            username=self.MOCK_USER_DATA["username"],
            course_run=self.course_runs[1],
            letter_grade="C",
            percent_grade=1.00,
        )
        self.user_grade_revoked_cert = UserGradeFactory(
            username=self.MOCK_USER_DATA["username"],
            course_run=self.course_runs[2],
            letter_grade="B",
            percent_grade=0.80,
        )
        self.course_certs = [
            CourseCertificateFactory(
                course_run=course_run,
                course_id=course_run.key,
                site=self.site,
            )
            for course_run in self.course_runs
        ]
        self.credential_content_type = ContentType.objects.get(app_label="credentials", model="coursecertificate")
        self.user_credentials = [
            UserCredentialFactory(
                username=self.MOCK_USER_DATA["username"],
                credential_content_type=self.credential_content_type,
                credential=course_cert,
            )
            for course_cert in self.course_certs
        ]
        self.user_credentials[2].status = UserCredential.REVOKED
        self.org_names = ["CCC", "AAA", "BBB"]
        self.orgs = [OrganizationFactory(name=name, site=self.site) for name in self.org_names]
        self.program = ProgramFactory(course_runs=self.course_runs, authoring_organizations=self.orgs, site=self.site)
        self.program_cert_record = ProgramCertRecordFactory.create(user=self.user, program=self.program)

    @patch("credentials.apps.records.views.SegmentClient", autospec=True)
    def test_404s_with_no_program_cert_record(self, segment_client):  # pylint: disable=unused-argument
        """Verify that the view 404s if a program cert record isn't found"""
        self.program_cert_record.delete()
        response = self.client.get(
            reverse("records:program_record_csv", kwargs={"uuid": self.program_cert_record.uuid.hex})
        )
        self.assertEqual(404, response.status_code)

    @ddt.data(True, False)
    @patch("credentials.apps.records.views.SegmentClient", autospec=True)
    @patch("credentials.apps.records.views.SegmentClient.track", autospec=True)
    def tests_creates_csv(self, segment_should_be_used, segment_client, track):  # pylint: disable=unused-argument
        """
        Verify that the csv parses and contains all of the necessary titles/headers.
        """
        if segment_should_be_used:
            self.site_configuration.segment_key = "the_key_to_the_apartment_where_the_money_will_be"
            self.site_configuration.save()
        response = self.client.get(
            reverse("records:program_record_csv", kwargs={"uuid": self.program_cert_record.uuid.hex})
        )
        self.assertEqual(bool(self.site_configuration.segment_key), segment_should_be_used)
        self.assertEqual(200, response.status_code)
        self.assertEqual(track.called, segment_should_be_used)
        content = response.content.decode("utf-8")
        csv_reader = csv.reader(io.StringIO(content))
        body = list(csv_reader)
        metadata_titles = [
            "Program Name",
            "Program Type",
            "Platform Provider",
            "Authoring Organization(s)",
            "Learner Name",
            "Username",
            "Email",
            "",
        ]
        # check the title of each metadata row
        for title in metadata_titles:
            self.assertEqual(title, body.pop(0)[0])
        csv_headers = body.pop(0)
        # Check that the header is present in the response bytestring
        headers = ["course_id", "percent_grade", "attempts", "school", "issue_date", "letter_grade", "name"]
        for header in headers:
            self.assertIn(header, csv_headers)

    @patch("credentials.apps.records.views.SegmentClient", autospec=True)
    def test_filename(self, segment_client):  # pylint: disable=unused-argument
        """
        Verify that the filename in response Content-Disposition is utf-8 encoded
        """
        re_expected = r'attachment; filename="test-user_test_program_[0-9a-z]+_grades\.csv"'

        response = self.client.get(
            reverse("records:program_record_csv", kwargs={"uuid": self.program_cert_record.uuid.hex})
        )
        actual = response["Content-Disposition"]

        self.assertTrue(re.fullmatch(re_expected, actual))

    def test_without_segment(self):
        """
        Verify this works without any Segment connection from the browser, even if there is a segment_key
        for the site.
        """
        self.site_configuration.segment_key = "xyzzy"
        self.site_configuration.save()
        response = self.client.get(
            reverse("records:program_record_csv", kwargs={"uuid": self.program_cert_record.uuid.hex})
        )

        self.assertEqual(200, response.status_code)


class LearnerRecordRedirectionTests(SiteMixin, TestCase):
    """
    Tests for the RecordsView and ProgramRecordsView views that ensure the system redirects learners' to the Learner
    Record MFE when making requests to the legacy views.
    """

    def setUp(self):
        super().setUp()
        self.user = UserFactory()
        self.client.login(username=self.user.username, password=USER_PASSWORD)
        self.program = ProgramFactory(site=self.site)
        self.pathway = PathwayFactory(site=self.site, programs=[self.program])
        self.pc = ProgramCertificateFactory(site=self.site, program_uuid=self.program.uuid)
        self.user_credential = UserCredentialFactory(username=self.user.username, credential=self.pc)
        self.pcr = ProgramCertRecordFactory(user=self.user, program=self.program, uuid=self.program.uuid)

    def test_redirect_on_accessing_record_view(self):
        """
        A unit test that ensures that a request to the `RecordsView` view will be redirected to the Learner Record MFE
        page (based on settings).
        """
        response = self.client.get(reverse("records:index"), follow=True)
        assert response.redirect_chain[-1][0] == settings.LEARNER_RECORD_MFE_RECORDS_PAGE_URL
        assert response.redirect_chain[-1][1] == 302

    def test_redirect_on_accessing_program_record_view_private(self):
        """
        A unit test that ensures that a request to the private `ProgramRecordsView` view will be redirected to the
        appropriate path/url of the Learner Record MFE.
        """
        response = self.client.get(
            reverse("records:private_programs", kwargs={"uuid": self.program.uuid.hex}), follow=True
        )
        assert response.redirect_chain[-1][0] == (
            f"{settings.LEARNER_RECORD_MFE_RECORDS_PAGE_URL}/{self.program.uuid.hex}"
        )
        assert response.redirect_chain[-1][1] == 302

    def test_redirect_on_accessing_program_record_view_public(self):
        """
        A unit test that ensures that a request to the public `ProgramRecordsView` view will be redirected to the
        appropriate path/url of the Learner Record MFE.
        """
        response = self.client.get(reverse("records:public_programs", kwargs={"uuid": self.pcr.uuid.hex}), follow=True)
        assert response.redirect_chain[-1][0] == (
            f"{settings.LEARNER_RECORD_MFE_RECORDS_PAGE_URL}/shared/{self.pcr.uuid.hex}"
        )
        assert response.redirect_chain[-1][1] == 302
