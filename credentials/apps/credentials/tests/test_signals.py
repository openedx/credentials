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
from openedx_events.learning.signals import PROGRAM_CERTIFICATE_AWARDED, PROGRAM_CERTIFICATE_REVOKED
from testfixtures import LogCapture

from credentials.apps.catalog.tests.factories import ProgramFactory
from credentials.apps.core.tests.factories import SiteConfigurationFactory, SiteFactory, UserFactory
from credentials.apps.credentials.constants import UserCredentialStatus
from credentials.apps.credentials.signals import listen_for_program_certificate_events, process_course_credential_event
from credentials.apps.credentials.tests.factories import ProgramCertificateFactory, UserCredentialFactory


@ddt.ddt
class CourseCertificateSignalTests(TestCase):
    """
    Tests for course certificate events consumed from the event bus.
    """

    class MockOpenEdXPublicSignal:
        def __init__(self, event_type):
            self.event_type = event_type

    def setUp(self):
        super().setUp()
        self.user = UserFactory()
        self.course_key = "course-v1:commander101+1T2023"
        self.mode = "verified"
        self.awarded_event_type = "org.openedx.learning.certificate.created.v1"
        self.revoked_event_type = "org.openedx.learning.certificate.revoked.v1"

    def _setup_event_data(self, event_type):
        certificate_data = CertificateData(
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
            current_status="",
            download_url="http://blah.blah.blah/certificate/1",
            name="hypnofrog",
        )
        event_metadata = EventsMetadata(
            event_type=event_type,
            id=uuid4(),
            minorversion=0,
            source="openedx/lms/web",
            sourcehost="lms.test",
            time=datetime.now(timezone.utc),
        )
        mock_event = self.MockOpenEdXPublicSignal(event_type)

        return {
            "certificate": certificate_data,
            "metadata": event_metadata,
            "signal": mock_event,
        }

    @patch("credentials.apps.credentials.signals.process_course_credential_update")
    def test_award_certificate_and_user_exists(self, mock_award):
        """
        Happy path. This test verifies the behavior of the signal receiver when a `CERTIFICATE_CREATED` event is
        consumed from the Event Bus.
        """
        expected_log_message = (
            f"Awarding a course certificate to user [{self.user.id}] in course run [{self.course_key}]"
        )

        event_data = self._setup_event_data(self.awarded_event_type)
        with LogCapture() as log:
            process_course_credential_event(None, **event_data)

        mock_award.assert_called_once_with(self.user, self.course_key, "verified", "awarded")
        assert log.records[0].msg == expected_log_message

    @patch("credentials.apps.credentials.signals.process_course_credential_update")
    def test_revoke_certificate_and_user_exists(self, mock_award):
        """
        Happy path. This test verifies the behavior of the signal receiver when a `CERTIFICATE_REVOKED` event is
        consumed from the Event Bus.
        """
        expected_log_message = (
            f"Revoking a course certificate from user [{self.user.id}] in course run [{self.course_key}]"
        )

        event_data = self._setup_event_data(self.revoked_event_type)
        with LogCapture() as log:
            process_course_credential_event(None, **event_data)

        mock_award.assert_called_once_with(self.user, self.course_key, "verified", "revoked")
        assert log.records[0].msg == expected_log_message

    @patch("credentials.apps.credentials.signals.get_or_create_user_from_event_data", return_value=(None, None))
    def test_certificate_exception_occurs(self, mock_get_user):  # pylint: disable=unused-argument
        """
        This test verifies the behavior of the `process_course_credential_update` function if an unexpected exception
        occurs when trying to retrieve (or create) a user while processing a `CERTIFICATE_CREATED` event from the Event
        Bus.
        """
        event_data = self._setup_event_data(self.awarded_event_type)

        expected_log_message = (
            f"Unable to process the `{self.awarded_event_type}` event with UUID {event_data['metadata'].id}: could "
            f"not retrieve or create a user with LMS user id [{event_data['certificate'].user.id}]"
        )

        with LogCapture() as log:
            process_course_credential_event(None, **event_data)

        assert log.records[0].msg == expected_log_message

    @ddt.data({}, {"certificate": True})
    def test_bad_data_type_passed_to_signal(self, bad_event_data):
        """
        This test verifies the behavior of the `process_course_credential_update` function when unexpected data is
        passed to the function.
        """
        expected_log_message = (
            "Unable to process course credential event from the Event Bus, the system received a null or unexpected "
            "CertificateData object."
        )

        with LogCapture() as log:
            process_course_credential_event(None, **bad_event_data)

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
        self.program_certificate_awarded_event_type = "org.openedx.learning.program.certificate.awarded.v1"
        self.program_certificate_revoked_event_type = "org.openedx.learning.program.certificate.revoked.v1"

    def _setup_event_data(self, certificate_status, event_type):
        program_certificate_data = ProgramCertificateData(
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
            status=certificate_status,
            url=f"https://{self.site.domain}/credentials/{str(self.user_credential.uuid).replace('-', '')}/",
        )
        event_metadata = EventsMetadata(
            event_type=event_type,
            id=uuid4(),
            minorversion=0,
            source="openedx/credentials",
            sourcehost="credentials.test",
            time=datetime.now(timezone.utc),
        )

        return {
            "program_certificate": program_certificate_data,
            "metadata": event_metadata,
        }

    @patch("credentials.apps.credentials.signals.get_producer")
    @override_settings(PROGRAM_CERTIFICATE_EVENTS_KAFKA_TOPIC_NAME="program-cert_publish_unit-test")
    def test_listen_for_program_certificate_awarded_event(self, mock_producer):
        event_data = self._setup_event_data(UserCredentialStatus.AWARDED, self.program_certificate_awarded_event_type)
        listen_for_program_certificate_events(None, PROGRAM_CERTIFICATE_AWARDED, **event_data)

        data = mock_producer.return_value.send.call_args.kwargs
        assert data["signal"].event_type == PROGRAM_CERTIFICATE_AWARDED.event_type
        assert data["event_data"]["program_certificate"] == event_data["program_certificate"]
        assert data["topic"] == "program-cert_publish_unit-test"
        assert data["event_key_field"] == "program_certificate.program.uuid"
        assert data["event_metadata"] == event_data["metadata"]

    @patch("credentials.apps.credentials.signals.get_producer")
    @override_settings(PROGRAM_CERTIFICATE_EVENTS_KAFKA_TOPIC_NAME="program-cert_publish_unit-test")
    def test_listen_for_program_certificate_revoked_event(self, mock_producer):
        event_data = self._setup_event_data(UserCredentialStatus.REVOKED, self.program_certificate_revoked_event_type)
        listen_for_program_certificate_events(None, PROGRAM_CERTIFICATE_REVOKED, **event_data)

        data = mock_producer.return_value.send.call_args.kwargs
        assert data["signal"].event_type == PROGRAM_CERTIFICATE_REVOKED.event_type
        assert data["event_data"]["program_certificate"] == event_data["program_certificate"]
        assert data["topic"] == "program-cert_publish_unit-test"
        assert data["event_key_field"] == "program_certificate.program.uuid"
        assert data["event_metadata"] == event_data["metadata"]
