"""
Models for the credentials service.
"""
import uuid
from collections import namedtuple

from django.contrib.contenttypes.fields import GenericForeignKey, GenericRelation
from django.contrib.contenttypes.models import ContentType
from django.contrib.sites.models import Site
from django.core.exceptions import ValidationError
from django.db import models
from django.urls import reverse
from django.utils.functional import cached_property
from django.utils.translation import ugettext_lazy as _
from django_extensions.db.models import TimeStampedModel
from opaque_keys import InvalidKeyError
from opaque_keys.edx.keys import CourseKey

from credentials.apps.core.utils import _choices
from credentials.apps.credentials import constants


def signatory_assets_path(instance, filename):
    """
    Returns path for signatory assets.

    Arguments:
        instance(Signatory): Signatory object
        filename(str): file to upload

    Returns:
        Path to asset.
    """
    return f'signatories/{instance.id}/{filename}'


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

    .. no_pii: This model has no PII.
    """
    site = models.ForeignKey(Site, on_delete=models.CASCADE)
    is_active = models.BooleanField(default=False)

    class Meta:
        abstract = True


class Signatory(TimeStampedModel):
    """
    Signatory model to add certificate signatories.

    .. no_pii: This model has no learner PII. The name used here is the name of the professor who signed the
    certificate.
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

    class Meta:
        verbose_name_plural = 'Signatories'

    def __str__(self):
        return f'{self.name}, {self.title}'

    def save(self, *args, **kwargs):  # pylint: disable=arguments-differ
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
            super().save(*args, **kwargs)
            self.image = temp_image

        super().save(force_update=True)


class AbstractCertificate(AbstractCredential):
    """
    Abstract Certificate configuration to support multiple type of certificates
    i.e. Programs, Courses.

    .. no_pii: This model has no PII.
    """
    signatories = models.ManyToManyField(Signatory)
    title = models.CharField(
        max_length=255, null=True, blank=True,
        help_text='Custom certificate title to override default display_name for a course/program.'
    )

    class Meta:
        abstract = True


class UserCredential(TimeStampedModel):
    """
    Credentials issued to a learner.

    .. pii: Stores username for a user.
        pii values: username
    .. pii_types: username
    .. pii_retirement: retained
    """
    AWARDED, REVOKED = (
        'awarded', 'revoked',
    )

    STATUSES_CHOICES = (
        (AWARDED, _('awarded')),
        (REVOKED, _('revoked')),
    )

    credential_content_type = models.ForeignKey(
        ContentType, limit_choices_to={'model__in': ('coursecertificate', 'programcertificate')},
        on_delete=models.CASCADE
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
        help_text=_('URL at which the credential can be downloaded')
    )
    uuid = models.UUIDField(default=uuid.uuid4, editable=False, unique=True)

    class Meta:
        unique_together = (('username', 'credential_content_type', 'credential_id'),)

    def get_absolute_url(self):
        return reverse('credentials:render', kwargs={'uuid': self.uuid.hex})

    def revoke(self):
        """ Sets the status to revoked, and saves this instance. """
        self.status = UserCredential.REVOKED
        self.save()


class CourseCertificate(AbstractCertificate):
    """
    Configuration for Course Certificates.

    .. no_pii: This model has no PII.
    """
    course_id = models.CharField(max_length=255, validators=[validate_course_key])
    certificate_type = models.CharField(
        max_length=255,
        choices=_choices(
            constants.CertificateType.HONOR,
            constants.CertificateType.PROFESSIONAL,
            constants.CertificateType.VERIFIED,
            constants.CertificateType.NO_ID_PROFESSIONAL,
        )
    )
    user_credentials = GenericRelation(
        UserCredential,
        content_type_field='credential_content_type',
        object_id_field='credential_id',
        related_query_name='course_credentials'
    )

    class Meta:
        unique_together = (('course_id', 'certificate_type', 'site'),)
        verbose_name = "Course certificate configuration"

    @cached_property
    def course_key(self):
        return CourseKey.from_string(self.course_id)


OrganizationDetails = namedtuple('OrganizationDetails', ('uuid', 'key', 'name', 'display_name',
                                                         'certificate_logo_image_url'))
ProgramDetails = namedtuple('ProgramDetails', ('uuid', 'title', 'subtitle', 'type', 'credential_title', 'course_count',
                                               'organizations', 'hours_of_effort'))


class ProgramCertificate(AbstractCertificate):
    """
    Configuration for Program Certificates.

    .. no_pii: This model has no PII.
    """

    program_uuid = models.UUIDField(db_index=True, null=False, blank=False, verbose_name=_('Program UUID'))
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
    include_hours_of_effort = models.BooleanField(
        default=False,
        help_text="Display the estimated total number of hours needed to complete all courses in the program. This "
                  "feature will only be displayed in the certificate if the attribute 'Total hours of effort' has "
                  "been set for the program in Discovery."
    )
    language = models.CharField(
        max_length=8,
        null=True,
        help_text='Locale in which certificates for this program will be rendered'
    )

    def __str__(self):
        return f'ProgramCertificate: {self.program_uuid}'

    class Meta:
        verbose_name = "Program certificate configuration"
        unique_together = (('site', 'program_uuid'),)

    def get_program_api_data(self):
        """ Returns program data from the Catalog API. """
        return self.site.siteconfiguration.get_program(self.program_uuid)  # pylint: disable=no-member

    # TODO: drop this query in favor of our local copy of
    #       catalog data (and start copying all data we need)
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
                certificate_logo_image_url=organization['certificate_logo_image_url']
            ))

        hours_of_effort = None
        if self.include_hours_of_effort:
            hours_of_effort = data.get('total_hours_of_effort')

        return ProgramDetails(
            uuid=data['uuid'],
            title=data['title'],
            subtitle=data['subtitle'],
            type=data['type'],
            credential_title=self.title,
            course_count=len(data['courses']),
            organizations=organizations,
            hours_of_effort=hours_of_effort
        )


class UserCredentialAttribute(TimeStampedModel):
    """
    Different attributes of User's Credential such as white list, grade etc.

    .. no_pii: This model has no PII.
    """
    user_credential = models.ForeignKey(UserCredential, related_name='attributes', on_delete=models.CASCADE)
    name = models.CharField(max_length=255)
    value = models.CharField(max_length=255)

    class Meta:
        unique_together = (('user_credential', 'name'),)
