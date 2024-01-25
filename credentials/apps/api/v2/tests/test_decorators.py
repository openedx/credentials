"""
Tests for the API app's `decorators.py` file.
"""

from django.conf import settings
from django.http import HttpResponse
from django.test import TestCase
from django.test.client import RequestFactory
from edx_toggles.toggles.testutils import override_waffle_switch
from testfixtures import LogCapture

from credentials.apps.api.v2.decorators import log_incoming_request
from credentials.apps.core.tests.factories import UserFactory


class CredentialsApiDecoratorTests(TestCase):
    """
    Unit tests for the API app's `decorators.py` file.
    """

    def setUp(self):
        super().setUp()
        self.request = RequestFactory().post("/api/v2/grades/")
        self.user = UserFactory()
        self.request.user = self.user

    def _test_view(self, request, *args, **kwargs):
        return HttpResponse("YOLO")

    @override_waffle_switch(settings.LOG_INCOMING_REQUESTS, active=True)
    def test_log_incoming_requests_decorator_waffle_enabled(self):
        """
        Test that ensures when a function decorated with the `log_incoming_requests` decorator, it emits the expected
        log messages if the setting gating the functionality is enabled.
        """
        expected_msg = (
            f"{self.request.method} request received to endpoint [{self.request.get_full_path()}] from user "
            f"[{self.request.user.username}] originating from [Unknown] with data: [{self.request.body}]"
        )
        decorated_view = log_incoming_request(self._test_view)

        args = (None, self.request)
        kwargs = {}
        with LogCapture() as log:
            decorated_view(*args, **kwargs)

        assert log.records[0].msg == expected_msg

    @override_waffle_switch(settings.LOG_INCOMING_REQUESTS, active=False)
    def test_log_incoming_requests_decorator_waffle_disabled(self):
        """
        Test that ensures when a function decorated with the `log_incoming_requests` decorator, it does not emit log
        messges if the setting gating the functionality is disabled.
        """
        decorated_view = log_incoming_request(self._test_view)

        args = (None, self.request)
        kwargs = {}
        with LogCapture() as log:
            decorated_view(*args, **kwargs)

        assert log.records == []

    @override_waffle_switch(settings.LOG_INCOMING_REQUESTS, active=True)
    def test_log_incoming_requests_decorator_with_exception(self):
        """
        Test that verifies an expected error message in our logs if an exception occurs when trying to log request data
        while using the `log_incoming_requests` decorator.
        """
        expected_msg = "Error logging incoming request: 'NoneType' object has no attribute 'body'. Continuing..."

        decorated_view = log_incoming_request(self._test_view)

        with LogCapture() as log:
            response = decorated_view(None, None)

        assert log.records[0].msg == expected_msg
        assert response.status_code == 200
        assert response.content == b"YOLO"
