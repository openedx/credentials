"""
Tests for the `signals.py` file of the Credentials Django app.
"""
from datetime import datetime, timezone
from unittest.mock import patch
from uuid import uuid4

import ddt
from django.test import TestCase, override_settings
from openedx_events.data import EventsMetadata
from openedx_events.learning.data import (
    CertificateData,
    CourseData,
    ProgramCertificateData,
    ProgramData,
    UserData,
    UserPersonalData,
)
from openedx_events.learning.signals import (
    CERTIFICATE_CREATED,
    PROGRAM_CERTIFICATE_AWARDED,
    PROGRAM_CERTIFICATE_REVOKED,
)
from testfixtures import LogCapture

from credentials.apps.catalog.tests.factories import ProgramFactory
from credentials.apps.core.tests.factories import SiteConfigurationFactory, SiteFactory, UserFactory
from credentials.apps.credentials.constants import UserCredentialStatus
from credentials.apps.credentials.signals import (
    _publish_program_certificate_event,
    award_certificate_from_event,
    listen_for_program_certificate_awarded_event,
    listen_for_program_certificate_revoked_event,
)
from credentials.apps.credentials.tests.factories import ProgramCertificateFactory, UserCredentialFactory


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


class ProgramCertificateEventLifecycleTests(TestCase):
    """
    Tests for publishing `PROGRAM_CERTIFICATE_AWARDED` and `PROGRAM_CERTIFICATE_REVOKED` events from the event bus.
    """

    def setUp(self):
        super().setUp()
        self.site = SiteFactory()
        self.site_configuration = SiteConfigurationFactory()
        self.program = ProgramFactory(site=self.site, uuid=uuid4())
        self.certificate = ProgramCertificateFactory(
            program_uuid=self.program.uuid,
            program=self.program,
            site=self.site,
        )
        self.user = UserFactory()
        self.user_credential = UserCredentialFactory(username=self.user.username, credential=self.certificate)

    def _create_program_certificate_event_data(self, status):
        return ProgramCertificateData(
            user=UserData(
                pii=UserPersonalData(
                    username=self.user.username, email=self.user.email, name=self.user.get_full_name()
                ),
                id=self.user.lms_user_id,
                is_active=self.user.is_active,
            ),
            program=ProgramData(
                uuid=str(self.program.uuid),
                title=self.program.title,
                program_type=self.program.type_slug,
            ),
            uuid=str(self.user_credential.uuid),
            status=status,
            url=f"https://{self.site.domain}/credentials/{str(self.user_credential.uuid).replace('-', '')}/",
        )

    def _create_event_metadata(self, event_type):
        return EventsMetadata(
            event_type=event_type.event_type,
            id=uuid4(),
            minorversion=0,
            source="openedx/credentials",
            sourcehost="credentials.test",
            time=datetime.now(timezone.utc),
        )

    @patch("credentials.apps.credentials.signals._publish_program_certificate_event")
    def test_listen_for_program_certificate_awarded_event(self, mock_publish):
        program_certificate_event_data = self._create_program_certificate_event_data(UserCredentialStatus.AWARDED)
        event_metadata = self._create_event_metadata(PROGRAM_CERTIFICATE_AWARDED)

        event_data = {"program_certificate": program_certificate_event_data, "metadata": event_metadata}
        listen_for_program_certificate_awarded_event(None, None, **event_data)

        assert mock_publish.called_once_with(
            PROGRAM_CERTIFICATE_AWARDED, program_certificate_event_data, event_metadata
        )

    @patch("credentials.apps.credentials.signals._publish_program_certificate_event")
    def test_listen_for_program_certificate_revoked_event(self, mock_publish):
        program_certificate_event_data = self._create_program_certificate_event_data(UserCredentialStatus.REVOKED)
        event_metadata = self._create_event_metadata(PROGRAM_CERTIFICATE_REVOKED)

        event_data = {"program_certificate": program_certificate_event_data, "metadata": event_metadata}
        listen_for_program_certificate_revoked_event(None, None, **event_data)

        assert mock_publish.called_once_with(
            PROGRAM_CERTIFICATE_REVOKED, program_certificate_event_data, event_metadata
        )

    @patch("credentials.apps.credentials.signals.get_producer")
    @override_settings(PROGRAM_CERTIFICATE_EVENTS_KAFKA_TOPIC_NAME="program-cert_publish_unit-test")
    def test_publish_program_certificate(self, mock_producer):
        program_certificate_event_data = self._create_program_certificate_event_data(UserCredentialStatus.AWARDED)
        event_metadata = self._create_event_metadata(PROGRAM_CERTIFICATE_AWARDED)

        _publish_program_certificate_event(PROGRAM_CERTIFICATE_AWARDED, program_certificate_event_data, event_metadata)

        data = mock_producer.return_value.send.call_args.kwargs
        assert data["signal"].event_type == PROGRAM_CERTIFICATE_AWARDED.event_type
        assert data["event_data"]["program_certificate"] == program_certificate_event_data
        assert data["topic"] == "program-cert_publish_unit-test"
        assert data["event_key_field"] == "program_certificate.program.uuid"
        assert data["event_metadata"] == event_metadata
