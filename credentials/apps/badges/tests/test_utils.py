import unittest

from attr import asdict
from datetime import datetime
from django.conf import settings
from unittest.mock import patch

from django.conf import settings
from openedx_events.learning.data import UserData, UserPersonalData, CourseData, CoursePassingStatusData
from opaque_keys.edx.keys import CourseKey

from credentials.apps.badges.checks import badges_checks
from credentials.apps.badges.credly.utils import get_credly_base_url, get_credly_api_base_url
from credentials.apps.badges.utils import ( 
    credly_check,
    extract_payload,
    get_event_type_keypaths,
    get_user_data, keypath,
    get_event_type_attr_type_by_keypath,
)

COURSE_PASSING_EVENT = "org.openedx.learning.course.passing.status.updated.v1"

class TestKeypath(unittest.TestCase):
    def test_keypath_exists(self):
        payload = {
            "course": {
                "key": "105-3332",
            }
        }
        result = keypath(payload, "course.key")
        self.assertEqual(result, "105-3332")

    def test_keypath_not_exists(self):
        payload = {
            "course": {
                "id": "105-3332",
            }
        }
        result = keypath(payload, "course.key")
        self.assertIsNone(result)

    def test_keypath_deep(self):
        payload = {"course": {"data": {"identification": {"id": 25}}}}
        result = keypath(payload, "course.data.identification.id")
        self.assertEqual(result, 25)

    def test_keypath_invalid_path(self):
        payload = {
            "course": {
                "key": "105-3332",
            }
        }
        result = keypath(payload, "course.id")
        self.assertIsNone(result)


class TestGetUserData(unittest.TestCase):
    def setUp(self):
        self.course_data_1 = CourseData(
            course_key="CS101",
            display_name="Introduction to Computer Science",
            start=datetime(2024, 4, 1),
            end=datetime(2024, 6, 1),
        )
        self.user_data_1 = UserData(
            id=1, is_active=True, pii=UserPersonalData(username="user1", email="user1@example.com", name="John Doe")
        )

        self.course_data_2 = CourseData(
            course_key="PHY101",
            display_name="Introduction to Physics",
            start=datetime(2024, 4, 15),
            end=datetime(2024, 7, 15),
        )
        self.user_data_2 = UserData(
            id=2, is_active=False, pii=UserPersonalData(username="user2", email="user2@example.com", name="Jane Doe")
        )

        self.passing_status_1 = {
            "course_passing_status": CoursePassingStatusData(
                is_passing=True, course=self.course_data_1, user=self.user_data_1
            )
        }

    def test_get_user_data_from_course_enrollment(self):
        result_1 = get_user_data(extract_payload(self.passing_status_1))
        self.assertIsNotNone(result_1)
        self.assertEqual(result_1.id, 1)
        self.assertTrue(result_1.is_active)
        self.assertEqual(result_1.pii.username, "user1")
        self.assertEqual(result_1.pii.email, "user1@example.com")
        self.assertEqual(result_1.pii.name, "John Doe")


class TestExtractPayload(unittest.TestCase):
    def setUp(self):
        self.course_data = CourseData(
            course_key="105-3332",
            display_name="Introduction to Computer Science",
            start=datetime(2024, 4, 1),
            end=datetime(2024, 6, 1),
        )

    def test_extract_payload(self):
        user_data = UserData(
            id=1, is_active=True, pii=UserPersonalData(username="user1", email="user1@example.com ", name="John Doe")
        )
        course_passing_status = CoursePassingStatusData(
            is_passing=True, course=self.course_data, user=user_data
        )
        public_signal_kwargs = {"course_passing_status": course_passing_status}
        result = extract_payload(public_signal_kwargs)
        self.assertIsNotNone(result)
        self.assertEqual(asdict(result), asdict(course_passing_status))

    def test_extract_payload_empty_payload(self):
        public_signal_kwargs = {"public_signal_kwargs": {}}
        result = extract_payload(**public_signal_kwargs)
        self.assertIsNone(result)


class TestBadgesChecks(unittest.TestCase):
    @patch("credentials.apps.badges.checks.get_badging_event_types")
    def test_badges_checks_empty_events(self, mock_get_badging_event_types):
        mock_get_badging_event_types.return_value = []
        errors = badges_checks()
        self.assertEqual(len(errors), 1)
        self.assertEqual(errors[0].msg, "BADGES_CONFIG['events'] must include at least one event.")
        self.assertEqual(errors[0].hint, "Add at least one event to BADGES_CONFIG['events'] setting.")
        self.assertEqual(errors[0].id, "badges.E001")

    @patch("credentials.apps.badges.checks.get_badging_event_types")
    def test_badges_checks_non_empty_events(self, mock_get_badging_event_types):
        mock_get_badging_event_types.return_value = ["event1", "event2"]
        errors = badges_checks()
        self.assertEqual(len(errors), 0)


class TestCredlyCheck(unittest.TestCase):
    def test_credly_configured(self):
        settings.BADGES_CONFIG = {
            "credly": {
                "CREDLY_BASE_URL": "https://www.credly.com",
                "CREDLY_API_BASE_URL": "https://api.credly.com",
                "CREDLY_SANDBOX_BASE_URL": "https://sandbox.credly.com",
                "CREDLY_SANDBOX_API_BASE_URL": "https://sandbox.api.credly.com",
                "USE_SANDBOX": True,
            }
        }
        result = credly_check()
        self.assertTrue(result)

    def test_credly_not_configured(self):
        settings.BADGES_CONFIG = {}
        result = credly_check()
        self.assertFalse(result)

    def test_credly_missing_keys(self):
        settings.BADGES_CONFIG = {
            "credly": {
                "CREDLY_BASE_URL": "https://www.credly.com",
                "CREDLY_API_BASE_URL": "https://api.credly.com",
                "USE_SANDBOX": True,
            }
        }
        result = credly_check()
        self.assertFalse(result)


class TestGetEventTypeKeypaths(unittest.TestCase):
    def test_get_event_type_keypaths(self):
        result = get_event_type_keypaths(COURSE_PASSING_EVENT)

        for ignored_keypath in settings.BADGES_CONFIG.get("rules", {}).get("ignored_keypaths", []):
            self.assertNotIn(ignored_keypath, result)

class TestGetCredlyBaseUrl(unittest.TestCase):
    def test_get_credly_base_url_sandbox(self):
        settings.BADGES_CONFIG["credly"] = {
            "CREDLY_BASE_URL": "https://www.credly.com",
            "CREDLY_SANDBOX_BASE_URL": "https://sandbox.credly.com",
            "USE_SANDBOX": True,
        }
        result = get_credly_base_url(settings)
        self.assertEqual(result, "https://sandbox.credly.com")

    def test_get_credly_base_url_production(self):
        settings.BADGES_CONFIG["credly"] = {
            "CREDLY_BASE_URL": "https://www.credly.com",
            "CREDLY_SANDBOX_BASE_URL": "https://sandbox.credly.com",
            "USE_SANDBOX": False,
        }
        result = get_credly_base_url(settings)
        self.assertEqual(result, "https://www.credly.com")


class TestGetCredlyApiBaseUrl(unittest.TestCase):
    def test_get_credly_api_base_url_sandbox(self):
        settings.BADGES_CONFIG["credly"] = {
            "CREDLY_API_BASE_URL": "https://api.credly.com",
            "CREDLY_SANDBOX_API_BASE_URL": "https://sandbox.api.credly.com",
            "USE_SANDBOX": True,
        }
    
        result = get_credly_api_base_url(settings)
        self.assertEqual(result, "https://sandbox.api.credly.com")

    def test_get_credly_api_base_url_production(self):
        settings.BADGES_CONFIG["credly"] = {
            "CREDLY_API_BASE_URL": "https://api.credly.com",
            "CREDLY_SANDBOX_API_BASE_URL": "https://sandbox.api.credly.com",
            "USE_SANDBOX": False,
        }
        result = get_credly_api_base_url(settings)
        self.assertEqual(result, "https://api.credly.com")


class TestGetEventTypeAttrTypeByKeypath(unittest.TestCase):
    def test_get_event_type_attr_type_by_keypath(self):
        keypath = "course.course_key"
        result = get_event_type_attr_type_by_keypath(COURSE_PASSING_EVENT, keypath)
        self.assertEqual(result, CourseKey)
    
    def test_get_event_type_attr_type_by_keypath_bool(self):
        keypath = "is_passing"
        result = get_event_type_attr_type_by_keypath(COURSE_PASSING_EVENT, keypath)
        self.assertEqual(result, bool)

    def test_get_event_type_attr_type_by_keypath_not_found(self):
        keypath = "course.id"
        result = get_event_type_attr_type_by_keypath(COURSE_PASSING_EVENT, keypath)
        self.assertIsNone(result)