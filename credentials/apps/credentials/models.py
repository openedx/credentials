"""
Models for the credentials service.
"""
# pylint: disable=model-missing-unicode
from __future__ import unicode_literals

import uuid  # pylint: disable=unused-import
from collections import namedtuple

from django.conf import settings
from django.contrib.contenttypes.fields import GenericForeignKey, GenericRelation
from django.contrib.contenttypes.models import ContentType
from django.contrib.sites.models import Site
from django.core.cache import cache
from django.core.exceptions import ValidationError
from django.core.urlresolvers import reverse
from django.db import models
from django.utils.functional import cached_property
from django.utils.translation import ugettext_lazy as _
from django_extensions.db.models import TimeStampedModel
from opaque_keys import InvalidKeyError
from opaque_keys.edx.keys import CourseKey

from credentials.apps.credentials import constants


def _choices(*values):
    """
    Helper for use with model field 'choices'.
    """
    return [(value,) * 2 for value in values]


def template_assets_path(instance, filename):
    """
    Returns path for credentials templates file assets.

    Arguments:
        instance(CertificateTemplateAsset): CertificateTemplateAsset object
        filename(str): file to upload

    Returns:
        Path to asset.
    """
    return 'certificate_template_assets/{id}/{filename}'.format(id=instance.id, filename=filename)


def signatory_assets_path(instance, filename):
    """
    Returns path for signatory assets.

    Arguments:
        instance(Signatory): Signatory object
        filename(str): file to upload

    Returns:
        Path to asset.
    """
    return 'signatories/{id}/{filename}'.format(id=instance.id, filename=filename)


def validate_image(image):
    """
    Validates that a particular image is small enough.
    """
    if image.size > (250 * 1024):
        raise ValidationError(_('The image file size must be less than 250KB.'))


def validate_course_key(course_key):
    """
    Validate the course_key is correct.
    """
    try:
        CourseKey.from_string(course_key)
    except InvalidKeyError:
        raise ValidationError(_("Invalid course key."))


class AbstractCredential(TimeStampedModel):
    """
    Abstract Credentials configuration model.
    """
    site = models.ForeignKey(Site)
    is_active = models.BooleanField(default=False)

    class Meta(object):
        abstract = True


class Signatory(TimeStampedModel):
    """
    Signatory model to add certificate signatories.
    """
    name = models.CharField(max_length=255)
    title = models.CharField(max_length=255)
    organization_name_override = models.CharField(
        max_length=255, null=True, blank=True,
        help_text=_('Signatory organization name if its different from issuing organization.')
    )
    image = models.ImageField(
        help_text=_(
            'Image must be square PNG files. The file size should be under 250KB.'
        ),
        upload_to=signatory_assets_path,
        validators=[validate_image]
    )

    class Meta(object):
        verbose_name_plural = 'Signatories'

    def __unicode__(self):
        return '{name}, {title}'.format(
            name=self.name,
            title=self.title
        )

    # pylint: disable=no-member
    def save(self, *args, **kwargs):
        """
        A primary key/ID will not be assigned until the model is written to
        the database. Given that our file path relies on this ID, save the
        model initially with no file. After the initial save, update the file
        and save again. All subsequent saves will write to the database only
        once.
        """
        if self.pk is None:
            temp_image = self.image
            self.image = None
            super(Signatory, self).save(*args, **kwargs)
            self.image = temp_image

        super(Signatory, self).save(force_update=True)


class CertificateTemplate(TimeStampedModel):
    """
    Certificate Template model to organize content for certificates.
    """

    name = models.CharField(max_length=255, db_index=True, unique=True)
    content = models.TextField(
        help_text=_('HTML Template content data.')
    )

    def __unicode__(self):
        return '{name}'.format(
            name=self.name
        )


class AbstractCertificate(AbstractCredential):  # pylint: disable=abstract-method
    """
    Abstract Certificate configuration to support multiple type of certificates
    i.e. Programs, Courses.
    """
    signatories = models.ManyToManyField(Signatory)
    template = models.ForeignKey(CertificateTemplate, null=True, blank=True)
    title = models.CharField(
        max_length=255, null=True, blank=True,
        help_text='Custom certificate title to override default display_name for a course/program.'
    )

    class Meta(object):
        abstract = True


class UserCredential(TimeStampedModel):
    """
    Credentials issued to a learner.
    """
    AWARDED, REVOKED = (
        'awarded', 'revoked',
    )

    STATUSES_CHOICES = (
        (AWARDED, _('awarded')),
        (REVOKED, _('revoked')),
    )

    credential_content_type = models.ForeignKey(
        ContentType, limit_choices_to={"model__in": ("coursecertificate", "programcertificate")}
    )
    credential_id = models.PositiveIntegerField()
    credential = GenericForeignKey('credential_content_type', 'credential_id')

    username = models.CharField(max_length=255, db_index=True)
    status = models.CharField(
        max_length=255,
        choices=_choices(
            constants.UserCredentialStatus.AWARDED,
            constants.UserCredentialStatus.REVOKED
        ),
        default=constants.UserCredentialStatus.AWARDED
    )
    download_url = models.CharField(
        max_length=255, blank=True, null=True,
        help_text=_('Download URL for the PDFs.')
    )
    uuid = models.UUIDField(default=uuid.uuid4, editable=False)

    class Meta(object):
        unique_together = (('username', 'credential_content_type', 'credential_id'),)

    def get_absolute_url(self):
        return reverse('credentials:render', kwargs={'uuid': self.uuid.hex})


class CourseCertificate(AbstractCertificate):
    """
    Configuration for Course Certificates.
    """
    course_id = models.CharField(max_length=255, validators=[validate_course_key])
    certificate_type = models.CharField(
        max_length=255,
        choices=_choices(
            constants.CertificateType.HONOR,
            constants.CertificateType.PROFESSIONAL,
            constants.CertificateType.VERIFIED
        )
    )
    user_credentials = GenericRelation(
        UserCredential,
        content_type_field='credential_content_type',
        object_id_field='credential_id',
        related_query_name='course_credentials'
    )

    class Meta(object):
        unique_together = (('course_id', 'certificate_type', 'site'),)
        verbose_name = "Course certificate configuration"


OrganizationDetails = namedtuple('OrganizationDetails', ('uuid', 'key', 'name', 'display_name', 'logo_image_url'))
ProgramDetails = namedtuple('ProgramDetails', ('uuid', 'title', 'type', 'course_count', 'organizations'))


class ProgramCertificate(AbstractCertificate):
    """
    Configuration for Program Certificates.
    """

    program_uuid = models.UUIDField(db_index=True, unique=True, null=True, blank=False, verbose_name=_('Program UUID'))
    program_id = models.PositiveIntegerField(db_index=True, unique=True,
                                             help_text='This field is DEPRECATED. Use program_uuid instead.')
    user_credentials = GenericRelation(
        UserCredential,
        content_type_field='credential_content_type',
        object_id_field='credential_id',
        related_query_name='program_credentials'
    )
    use_org_name = models.BooleanField(
        default=False,
        help_text=_("Display the associated organization's name (e.g. ACME University) "
                    "instead of its short name (e.g. ACMEx)"),
        verbose_name=_('Use organization name')
    )

    def __str__(self):
        return 'ProgramCertificate: {uuid}'.format(uuid=(self.program_uuid or self.program_id))

    class Meta(object):
        verbose_name = "Program certificate configuration"

    def get_program_api_data(self):
        """ Returns program data from the Catalog API. """
        program_uuid = self.program_uuid.hex
        cache_key = 'programs.api.data.{uuid}'.format(uuid=program_uuid)
        program = cache.get(cache_key)

        if program:
            return program

        client = self.site.siteconfiguration.catalog_api_client
        program = client.programs(program_uuid).get()
        cache.set(cache_key, program, settings.PROGRAMS_CACHE_TTL)

        return program

    @cached_property
    def program_details(self):
        """ Returns details about the program associated with this certificate. """
        data = self.get_program_api_data()

        organizations = []
        for organization in data['authoring_organizations']:
            organizations.append(OrganizationDetails(
                uuid=organization['uuid'],
                key=organization['key'],
                name=organization['name'],
                display_name=organization['name'] if self.use_org_name else organization['key'],
                logo_image_url=organization['logo_image_url']
            ))

        return ProgramDetails(
            uuid=data['uuid'],
            title=data['title'],
            type=data['type'],
            course_count=len(data['courses']),
            organizations=organizations
        )


class UserCredentialAttribute(TimeStampedModel):
    """
    Different attributes of User's Credential such as white list, grade etc.
    """
    user_credential = models.ForeignKey(UserCredential, related_name='attributes')
    name = models.CharField(max_length=255)
    value = models.CharField(max_length=255)

    class Meta(object):
        unique_together = (('user_credential', 'name'),)


class CertificateTemplateAsset(TimeStampedModel):
    """
    Certificate Template Asset model to add content files for a certificate
    template.
    """
    name = models.CharField(max_length=255)
    asset_file = models.FileField(upload_to=template_assets_path)

    def __unicode__(self):
        """Unicode representation. """
        return '{name}'.format(
            name=self.name
        )

    # pylint: disable=no-member
    def save(self, *args, **kwargs):
        """
        A primary key/ID will not be assigned until the model is written to
        the database. Given that our file path relies on this ID, save the
        model initially with no file. After the initial save, update the file
        and save again. All subsequent saves will write to the database only
        once.
        """
        if self.pk is None:
            temp_file = self.asset_file
            self.asset_file = None
            super(CertificateTemplateAsset, self).save(*args, **kwargs)
            self.asset_file = temp_file

        super(CertificateTemplateAsset, self).save(force_update=True)
