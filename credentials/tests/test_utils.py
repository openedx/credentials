import platform
import sys
import unittest

from logging.handlers import SysLogHandler
from os import path
from unittest.mock import patch

from django.core.exceptions import ImproperlyConfigured

from credentials.settings.utils import get_env_setting, get_logger_config, str2bool


class TestGetEnvSetting(unittest.TestCase):
    @patch.dict("os.environ", {"TEST_SETTING": "test_value"})
    def test_get_env_setting_existing_setting(self):
        result = get_env_setting("TEST_SETTING")
        self.assertEqual(result, "test_value")

    @patch.dict("os.environ", {})
    def test_get_env_setting_missing_setting(self):
        with self.assertRaises(ImproperlyConfigured):
            get_env_setting("MISSING_SETTING")


class TestGetLoggerConfig(unittest.TestCase):
    def test_default_config(self):
        config = get_logger_config()
        self.assertEqual(config["version"], 1)
        self.assertFalse(config["disable_existing_loggers"])
        self.assertIn("standard", config["formatters"])
        self.assertIn("syslog_format", config["formatters"])
        self.assertIn("raw", config["formatters"])
        self.assertIn("console", config["handlers"])
        self.assertIn("django", config["loggers"])
        self.assertIn("requests", config["loggers"])
        self.assertIn("factory", config["loggers"])
        self.assertIn("django.request", config["loggers"])
        self.assertIn("", config["loggers"])

    def test_dev_env_true(self):
        config = get_logger_config(dev_env=True)
        self.assertIn("local", config["handlers"])
        self.assertEqual(config["handlers"]["local"]["class"], "logging.handlers.RotatingFileHandler")
        self.assertEqual(config["handlers"]["local"]["level"], "INFO")
        self.assertEqual(config["handlers"]["local"]["formatter"], "standard")
        self.assertEqual(config["handlers"]["local"]["filename"], path.join("/var/tmp", "edx.log"))
        self.assertEqual(config["handlers"]["local"]["maxBytes"], 1024 * 1024 * 2)
        self.assertEqual(config["handlers"]["local"]["backupCount"], 5)

    def test_dev_env_false(self):
        config = get_logger_config(dev_env=False)
        self.assertIn("local", config["handlers"])
        self.assertEqual(config["handlers"]["local"]["level"], "INFO")
        self.assertEqual(config["handlers"]["local"]["class"], "logging.handlers.SysLogHandler")
        self.assertEqual(
            config["handlers"]["local"]["address"], "/var/run/syslog" if sys.platform == "darwin" else "/dev/log"
        )
        self.assertEqual(config["handlers"]["local"]["formatter"], "syslog_format")
        self.assertEqual(config["handlers"]["local"]["facility"], SysLogHandler.LOG_LOCAL0)

    def test_debug_true(self):
        config = get_logger_config(debug=True)
        self.assertEqual(config["handlers"]["console"]["level"], "DEBUG")

    def test_debug_false(self):
        config = get_logger_config(debug=False)
        self.assertEqual(config["handlers"]["console"]["level"], "INFO")

    def test_local_loglevel_invalid(self):
        config = get_logger_config(local_loglevel="INVALID")
        self.assertEqual(config["handlers"]["local"]["level"], "INFO")

    def test_local_loglevel_info(self):
        config = get_logger_config(local_loglevel="INFO")
        self.assertEqual(config["handlers"]["local"]["level"], "INFO")

    def test_local_loglevel_debug(self):
        config = get_logger_config(local_loglevel="DEBUG")
        self.assertEqual(config["handlers"]["local"]["level"], "DEBUG")

    def test_local_loglevel_warning(self):
        config = get_logger_config(local_loglevel="WARNING")
        self.assertEqual(config["handlers"]["local"]["level"], "WARNING")

    def test_local_loglevel_error(self):
        config = get_logger_config(local_loglevel="ERROR")
        self.assertEqual(config["handlers"]["local"]["level"], "ERROR")

    def test_local_loglevel_critical(self):
        config = get_logger_config(local_loglevel="CRITICAL")
        self.assertEqual(config["handlers"]["local"]["level"], "CRITICAL")

    def test_hostname(self):
        config = get_logger_config()
        hostname = platform.node().split(".")[0]
        self.assertIn(hostname, config["formatters"]["syslog_format"]["format"])

    def test_service_variant(self):
        config = get_logger_config()
        self.assertIn("service_variant=credentials", config["formatters"]["syslog_format"]["format"])

    def test_logging_env(self):
        config = get_logger_config()
        self.assertIn("env:no_env", config["formatters"]["syslog_format"]["format"])

    def test_edx_filename(self):
        config = get_logger_config(dev_env=True)
        self.assertIn("/var/tmp/edx.log", config["handlers"]["local"]["filename"])

    def test_edx_filename_not_used(self):
        config = get_logger_config(dev_env=False)
        self.assertNotIn("filename", config["handlers"]["local"])

    def test_invalid_platform(self):
        original_platform = sys.platform
        sys.platform = "invalid"
        config = get_logger_config(dev_env=False)
        self.assertEqual(config["handlers"]["local"]["address"], "/dev/log")
        sys.platform = original_platform


class TestStr2Bool(unittest.TestCase):
    def test_str2bool_true(self):
        result = str2bool("true")
        self.assertTrue(result)

    def test_str2bool_false(self):
        result = str2bool("false")
        self.assertFalse(result)

    def test_str2bool_yes(self):
        result = str2bool("yes")
        self.assertTrue(result)

    def test_str2bool_no(self):
        result = str2bool("no")
        self.assertFalse(result)

    def test_str2bool_t(self):
        result = str2bool("t")
        self.assertTrue(result)

    def test_str2bool_f(self):
        result = str2bool("f")
        self.assertFalse(result)

    def test_str2bool_1(self):
        result = str2bool("1")
        self.assertTrue(result)

    def test_str2bool_0(self):
        result = str2bool("0")
        self.assertFalse(result)

    def test_str2bool_case_insensitive(self):
        result = str2bool("TrUe")
        self.assertTrue(result)
        result = str2bool("FaLsE")
        self.assertFalse(result)
