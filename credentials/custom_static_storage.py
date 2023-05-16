from django.contrib.staticfiles.storage import ManifestStaticFilesStorage
from django.utils.functional import cached_property


class CustomStaticFilesStorage(ManifestStaticFilesStorage):
    @cached_property
    def manifest_strict(self):
        return False
