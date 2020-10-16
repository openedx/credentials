"""
Custom S3 storage backends to store files in sub folders.
"""
from functools import partial

from django.conf import settings
from storages.backends.s3boto import S3BotoStorage
from storages.backends.s3boto3 import S3Boto3Storage

# TODO: remove once we've switched to boto3
MediaS3BotoStorage = partial(
    S3BotoStorage,
    location=settings.MEDIA_ROOT.strip('/')
)

MediaS3Boto3Storage = partial(
    S3Boto3Storage,
    location=settings.MEDIA_ROOT.strip('/')
)

# TODO: remove once we've switched to boto3 (it doesn't seem to be used anywhere)
StaticS3BotoStorage = partial(
    S3BotoStorage,
    location=settings.STATIC_ROOT.strip('/')
)
