"""
Custom S3 storage backends to store files in sub folders.
"""
from functools import partial

from boto.s3.connection import S3Connection
from django.conf import settings
from storages.backends.s3boto import S3BotoStorage


class S3NoSecurityTokenConnection(S3Connection):
    """
    Workaround for https://github.com/boto/boto/issues/1477

    This is done to suppress boto's default behavior of generating unwanted
    query strings in s3 URLs when used in AWS accounts with certain SigV4
    configurations.
    """
    def __init__(self, *a, **kw):
        super(S3NoSecurityTokenConnection, self).__init__(*a, **kw)
        self.provider.security_token = ""


MediaS3BotoStorage = partial(
    S3BotoStorage,
    location=settings.MEDIA_ROOT.strip('/'),
    connection_class=S3NoSecurityTokenConnection
)

StaticS3BotoStorage = partial(
    S3BotoStorage,
    location=settings.STATIC_ROOT.strip('/'),
    connection_class=S3NoSecurityTokenConnection
)
