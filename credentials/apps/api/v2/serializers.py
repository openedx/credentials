"""
Serializers for data manipulated by the credentials service APIs.
"""

import logging
from typing import TYPE_CHECKING

from django.core.exceptions import ObjectDoesNotExist
from rest_framework import serializers
from rest_framework.exceptions import ValidationError
from rest_framework.reverse import reverse

import credentials.apps.catalog.api
from credentials.apps.api.accreditors import Accreditor
from credentials.apps.catalog.models import CourseRun
from credentials.apps.credentials.constants import UserCredentialStatus
from credentials.apps.credentials.models import (
    CourseCertificate,
    ProgramCertificate,
    UserCredential,
    UserCredentialAttribute,
    UserCredentialDateOverride,
)
from credentials.apps.records.models import UserGrade

if TYPE_CHECKING:
    from credentials.apps.credentials.models import AbstractCertificate


logger = logging.getLogger(__name__)


class CredentialField(serializers.Field):
    """Field identifying the credential type and identifiers."""

    def to_internal_value(self, data) -> "AbstractCertificate":
        site = self.context["request"].site

        program_uuid = data.get("program_uuid")
        if program_uuid:
            try:
                return ProgramCertificate.objects.get(program_uuid=program_uuid, is_active=True)
            except ObjectDoesNotExist:
                msg = f"No active ProgramCertificate exists for program [{program_uuid}]"
                logger.error(msg)
                raise ValidationError({"program_uuid": msg})

        course_run_key = data.get("course_run_key")
        if not course_run_key:
            raise ValidationError("Credential identifier is missing.")

        # If we get this far, we necessarily have a course_run_key
        course_runs = credentials.apps.catalog.api.get_course_runs_by_course_run_keys([course_run_key])
        if course_runs:
            course_run = course_runs[0]
            if self.read_only:
                try:
                    cert = CourseCertificate.objects.get(course_run=course_run, site=site)
                except ObjectDoesNotExist:
                    cert = None
            else:
                # Create course cert on the fly, but don't upgrade it to active if it's manually been turned off
                cert, _ = CourseCertificate.objects.get_or_create(
                    course_id=course_run_key,
                    course_run=course_run,
                    site=site,
                    defaults={
                        "is_active": True,
                        "certificate_type": data.get("mode"),
                    },
                )
            if cert is None or not cert.is_active:
                msg = f"No active CourseCertificate exists for course run [{course_run_key}]"
                raise ValidationError({"course_run_key": msg})
            return cert
        elif self.read_only:
            msg = f"No active CourseCertificate exists for course run [{course_run_key}]"
            raise ValidationError({"course_run_key": msg})
        else:
            msg = (
                f"CourseCertificate failed to create because the CourseRun {course_run_key} doesn't exist "
                "in the catalog"
            )
            raise ValidationError({"course_run_key": msg})

    def to_representation(self, value):
        """Serialize objects to a according to model content-type."""
        if hasattr(value, "program_uuid"):
            credential = {
                "type": "program",
                "credential_id": value.id,
                "program_uuid": value.program_uuid,
            }
        else:  # course run
            credential = {
                "type": "course-run",
                "course_run_key": value.course_run.key,
                "mode": value.certificate_type,
            }

        return credential


class UserCertificateURLField(serializers.ReadOnlyField):  # pylint: disable=abstract-method
    """Field for UserCredential URL pointing html view"""

    def to_representation(self, value):
        """Build the UserCredential URL for html view. Get the current domain from request."""
        return reverse(
            "credentials:render",
            kwargs={
                "uuid": value.hex,
            },
            request=self.context["request"],
        )


class CourseRunField(serializers.Field):
    """Field for CourseRun foreign keys"""

    def to_internal_value(self, data):
        site = self.context["request"].site
        try:
            # TODO use the catalog API, not direct reference
            return CourseRun.objects.get(key=data, course__site=site)
        except ObjectDoesNotExist:
            msg = f"No CourseRun exists for key [{data}]"
            logger.error(msg)
            raise ValidationError(msg)

    def to_representation(self, value):
        """Build the CourseRun for html view."""
        return value.key


class UserCredentialAttributeSerializer(serializers.ModelSerializer):
    """Serializer for CredentialAttribute objects"""

    class Meta:
        model = UserCredentialAttribute
        fields = ("name", "value")


class UserCredentialDateOverrideSerializer(serializers.ModelSerializer):
    """Serializer for UserCredentialDateOverride objects"""

    class Meta:
        model = UserCredentialDateOverride
        fields = ("date",)


class UserCredentialSerializer(serializers.ModelSerializer):
    """Serializer for UserCredential objects."""

    credential = CredentialField(read_only=True)
    attributes = UserCredentialAttributeSerializer(many=True, read_only=True)
    date_override = UserCredentialDateOverrideSerializer(required=False, allow_null=True)
    certificate_url = UserCertificateURLField(source="uuid", read_only=True)

    class Meta:
        model = UserCredential
        fields = (
            "username",
            "credential",
            "status",
            "uuid",
            "attributes",
            "date_override",
            "created",
            "modified",
            "certificate_url",
        )
        read_only_fields = (
            "username",
            "uuid",
            "created",
            "modified",
        )


class UserCredentialCreationSerializer(serializers.ModelSerializer):
    """Serializer used to create UserCredential objects."""

    credential = CredentialField()
    attributes = UserCredentialAttributeSerializer(many=True, required=False)
    date_override = UserCredentialDateOverrideSerializer(required=False, allow_null=True)
    certificate_url = UserCertificateURLField(source="uuid")

    # This field is not part of the Model, so we add it here to use in the create step.
    # it is write_only so that we do not attempt to show it in the API response.
    lms_user_id = serializers.CharField(write_only=True, required=False)

    def validate_attributes(self, value):
        """Check that the name attributes cannot be duplicated."""
        names = [attribute["name"] for attribute in value]

        if len(names) != len(set(names)):
            raise ValidationError("Attribute names cannot be duplicated.")

        return value

    def issue_credential(self, validated_data):
        """
        Issue a new credential.

        Args:
            validated_data (dict): Input data specifying the credential type, recipient, and attributes.

        Returns:
            AbstractCredential
        """
        accreditor = Accreditor()
        credential = validated_data["credential"]
        username = validated_data["username"]
        status = validated_data.get("status", UserCredentialStatus.AWARDED)
        attributes = validated_data.pop("attributes", None)
        date_override = validated_data.pop("date_override", None)
        lms_user_id = validated_data.pop("lms_user_id", None)
        request = self.context.get("request")
        return accreditor.issue_credential(
            credential,
            username,
            status=status,
            attributes=attributes,
            date_override=date_override,
            request=request,
            lms_user_id=lms_user_id,
        )

    def create(self, validated_data):
        return self.issue_credential(validated_data)

    class Meta:
        model = UserCredential
        fields = UserCredentialSerializer.Meta.fields + ("lms_user_id",)
        read_only_fields = (
            "uuid",
            "created",
            "modified",
        )


class UserGradeSerializer(serializers.ModelSerializer):
    """Serializer for UserGrade objects."""

    course_run = CourseRunField()

    class Meta:
        model = UserGrade
        fields = (
            "id",
            "username",
            "course_run",
            "letter_grade",
            "percent_grade",
            "verified",
            "lms_last_updated_at",
            "created",
            "modified",
        )
        read_only_fields = (
            "id",
            "created",
            "modified",
        )
        # turn off validation, it only tries to complain about unique_together when updating existing objects
        validators = []

    def is_valid(self, *, raise_exception=False):
        # The LMS sometimes gives us None for the letter grade for some reason. But since the model doesn't take null,
        # just convert it into an empty string instead.
        if self.initial_data.get("letter_grade", "") is None:
            self.initial_data["letter_grade"] = ""

        return super().is_valid(raise_exception=raise_exception)

    def create(self, validated_data):
        # If these next two are missing, the serializer will have already caught the error
        username = validated_data.get("username")
        course_run = validated_data.get("course_run")

        # Support updating or creating when posting to a grade endpoint, since clients don't necessarily know the
        # resource ID to use and we don't need to make them care.
        grade, _ = UserGrade.objects.update_or_create(
            username=username,
            course_run=course_run,
            defaults=validated_data,
        )

        logger.info(
            f"Updated grade for user [{username}] in course [{course_run.key}] with percent_grade "
            f"[{grade.percent_grade}], letter_grade [{grade.letter_grade}], verified [{grade.verified}], and "
            f"lms_last_updated_at [{grade.lms_last_updated_at}]"
        )

        return grade


class CourseCertificateSerializer(serializers.ModelSerializer):
    course_run = CourseRunField(read_only=True)

    class Meta:
        model = CourseCertificate
        fields = (
            "id",
            "site",
            "course_id",
            "course_run",
            "certificate_type",
            "certificate_available_date",
            "is_active",
        )
        read_only_fields = ("id", "course_run", "site")

    def create(self, validated_data):
        site = self.context["request"].site
        # A course run may not exist, but if it does, we want to find it. There may be times where course
        # staff will change the date on a newly created course before credentials has pulled it from the catalog.
        course_id = validated_data["course_id"]
        course_run = None
        try:
            # TODO use the catalog API, not direct reference
            course_run = CourseRun.objects.get(key=course_id)
        except ObjectDoesNotExist:
            logger.warning(
                "Course run certificate failed to create "
                f"because the course run [{course_id}] doesn't exist in the catalog"
            )
        # Check if the cert already exists, attempt to update the course_run and cert date
        cert, _ = CourseCertificate.objects.update_or_create(
            course_id=course_id,
            site=site,
            certificate_type=validated_data["certificate_type"],
            defaults={
                "is_active": validated_data["is_active"],
                "course_run": course_run,
                "certificate_available_date": validated_data["certificate_available_date"],
            },
        )
        return cert
