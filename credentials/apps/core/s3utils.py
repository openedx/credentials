"""
Custom S3 storage backends to store files in sub folders.
"""
from functools import partial

from django.conf import settings
from storages.backends.s3boto import S3BotoStorage

MediaS3BotoStorage = partial(S3BotoStorage, location=settings.MEDIA_ROOT.strip("/"))

StaticS3BotoStorage = partial(S3BotoStorage, location=settings.STATIC_ROOT.strip("/"))
