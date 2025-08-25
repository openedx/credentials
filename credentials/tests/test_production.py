import builtins
import importlib
import io
import sys
import types


def test_production_storage_from_yaml(monkeypatch):
    """Test that YAML config correctly populates STORAGES and FILE_STORAGE_BACKEND."""

    def fake_get_env_setting(key):
        if key == "CREDENTIALS_CFG":
            return "/fake/path/config.yaml"
        return ""

    class FakeSettingsType:
        PRODUCTION = "production"

    fake_yaml_content = """
        DEFAULT_FILE_STORAGE: storages.backends.s3boto3.S3Boto3Storage
        STATICFILES_STORAGE: storage.ManifestStaticFilesStorage
        MEDIA_ROOT: /tmp/media
        MEDIA_URL: /media/
    """

    sys.modules.pop("credentials.settings.production", None)

    monkeypatch.setitem(
        sys.modules,
        "credentials.settings.utils",
        types.SimpleNamespace(
            get_env_setting=fake_get_env_setting,
            get_logger_config=lambda *a, **kw: {},
        ),
    )
    monkeypatch.setitem(
        sys.modules,
        "credentials.apps.plugins.constants",
        types.SimpleNamespace(
            PROJECT_TYPE="credentials.djangoapp",
            SettingsType=FakeSettingsType,
        ),
    )
    monkeypatch.setitem(
        sys.modules,
        "edx_django_utils.plugins",
        types.SimpleNamespace(add_plugins=lambda *a, **kw: None),
    )

    monkeypatch.setattr(builtins, "open", lambda *a, **kw: io.StringIO(fake_yaml_content))

    prod = importlib.import_module("credentials.settings.production")

    assert not hasattr(prod, "DEFAULT_FILE_STORAGE")
    assert not hasattr(prod, "STATICFILES_STORAGE")

    assert "default" in prod.STORAGES
    assert prod.STORAGES["default"]["BACKEND"] == "storages.backends.s3boto3.S3Boto3Storage"
    assert "staticfiles" in prod.STORAGES
    assert prod.STORAGES["staticfiles"]["BACKEND"] == "storage.ManifestStaticFilesStorage"
