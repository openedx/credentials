"""
Tests for the `signals.py` file of the Credentials Django app.
"""
from datetime import datetime, timezone
from unittest.mock import patch
from uuid import uuid4

import ddt
from django.test import TestCase
from openedx_events.data import EventsMetadata
from openedx_events.learning.data import CertificateData, CourseData, UserData, UserPersonalData
from openedx_events.learning.signals import CERTIFICATE_CREATED
from testfixtures import LogCapture

from credentials.apps.core.tests.factories import UserFactory
from credentials.apps.credentials.signals import award_certificate_from_event


@ddt.ddt
class CertificateCreatedSignalTests(TestCase):
    """
    Tests for consuming `CERTIFICATE_CREATED` events from the event bus.
    """

    def setUp(self):
        super().setUp()
        self.user = UserFactory()
        self.course_key = "course-v1:commander101+1T2023"
        self.mode = "verified"
        self.certificate_data = CertificateData(
            user=UserData(
                pii=UserPersonalData(
                    username=self.user.username,
                    email=self.user.email,
                    name=f"{self.user.first_name} {self.user.last_name}",
                ),
                id=self.user.lms_user_id,
                is_active=True,
            ),
            course=CourseData(
                course_key=self.course_key,
            ),
            mode=self.mode,
            grade="1.0",
            current_status="downloadable",
            download_url="http://blah.blah.blah/certificate/1",
            name="hypnofrog",
        )
        self.event_metadata = EventsMetadata(
            event_type=CERTIFICATE_CREATED.event_type,
            id=uuid4(),
            minorversion=0,
            source="openedx/lms/web",
            sourcehost="lms.test",
            time=datetime.now(timezone.utc),
        )
        self.event_data = {"certificate": self.certificate_data, "metadata": self.event_metadata}

    @patch("credentials.apps.credentials.signals.award_course_certificate")
    def test_certificate_created_user_exists(self, mock_award):
        """
        Happy path. This test verifies the ability to extract required data from a `CERTIFICATE_CREATED` event consumed
        from the event bus. It then verifies the data passed to the `award_certificate_from_event` utility function
        matches what we would expect.
        """
        expected_log_message = (
            f"Awarding a course certificate to user [{self.user.id}] in course run [{self.course_key}]"
        )

        with LogCapture() as log:
            award_certificate_from_event(None, **self.event_data)

        mock_award.assert_called_once_with(self.user, self.course_key, "verified")
        assert log.records[0].msg == expected_log_message

    @patch("credentials.apps.credentials.signals.get_or_create_user_from_event_data", return_value=(None, None))
    def test_certificate_exception_occurs(self, mock_get_user):  # pylint: disable=unused-argument
        """
        This test verifies the behavior of the `award_certificate_from_event` function if an unexpected exception occurs
        when trying to retrieve (or create) a user while processing a `CERTIFICATE_CREATED` event from the event bus.
        """
        expected_log_message = (
            f"Failed to award a course certificate to user with (LMS) user id [{self.user.lms_user_id}] in course run "
            f"[{self.course_key}]. Could not retrieve or create a user in Credentials associated with the given user"
        )

        with LogCapture() as log:
            award_certificate_from_event(None, **self.event_data)

        assert log.records[0].msg == expected_log_message

    @ddt.data({}, {"certificate": True})
    def test_bad_data_type_passed_to_signal(self, bad_event_data):
        """
        This test verifies the behavior of the `award_certificate_from_event` function when unexpected data is passed
        to the function.
        """
        expected_log_message = "Received null or unexpected data type from CERTIFICATE_CREATED signal"

        with LogCapture() as log:
            award_certificate_from_event(None, **bad_event_data)

        assert log.records[0].msg == expected_log_message
