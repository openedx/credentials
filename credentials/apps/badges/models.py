"""
Badges DB models.
"""

import logging
import operator
import uuid

from django.conf import settings
from django.db import models
from django.utils.translation import gettext_lazy as _
from django_extensions.db.models import TimeStampedModel
from model_utils import Choices
from model_utils.fields import StatusField
from openedx_events.learning.data import BadgeData, BadgeTemplateData, UserData, UserPersonalData

from credentials.apps.badges.credly.utils import get_credly_base_url
from credentials.apps.badges.signals.signals import (
    notify_progress_complete,
    notify_progress_incomplete,
    notify_requirement_fulfilled,
    notify_requirement_regressed,
)
from credentials.apps.badges.utils import keypath
from credentials.apps.core.api import get_user_by_username
from credentials.apps.credentials.models import AbstractCredential, UserCredential


logger = logging.getLogger(__name__)


class CredlyOrganization(TimeStampedModel):
    """
    Credly Organization configuration.
    """

    uuid = models.UUIDField(unique=True, help_text=_("Put your Credly Organization ID here."))
    api_key = models.CharField(
        max_length=255,
        help_text=_("Credly API shared secret for Credly Organization."),
        blank=True,
    )
    name = models.CharField(
        max_length=255,
        null=True,
        blank=True,
        help_text=_("Verbose name for Credly Organization."),
    )

    def __str__(self):
        return f"{self.name or self.uuid}"

    @classmethod
    def get_all_organization_ids(cls):
        """
        Get all organization IDs.
        """
        return list(cls.objects.values_list("uuid", flat=True))

    @classmethod
    def get_preconfigured_organizations(cls):
        """
        Get preconfigured organizations.
        """
        return settings.BADGES_CONFIG["credly"].get("ORGANIZATIONS", {})

    @property
    def is_preconfigured(self):
        """
        Checks if the organization is preconfigured.
        """

        return str(self.uuid) in CredlyOrganization.get_preconfigured_organizations().keys()


class BadgeTemplate(AbstractCredential):
    """
    Describes badge template credential type.

    NOTE: currently hidden in the admin as a base class (see more details on the CredlyBadgeTemplate).
    """

    ORIGIN = "openedx"

    STATES = Choices("draft", "active", "archived")

    uuid = models.UUIDField(unique=True, default=uuid.uuid4, help_text=_("Unique badge template ID."))
    name = models.CharField(max_length=255, help_text=_("Badge template name."))
    description = models.TextField(null=True, blank=True, help_text=_("Badge template description."))
    icon = models.ImageField(upload_to="badge_templates/icons", null=True, blank=True)
    origin = models.CharField(max_length=128, null=True, blank=True, help_text=_("Badge template type."))
    state = StatusField(
        choices_name="STATES",
        help_text=_("Credly badge template state (auto-managed)."),
    )

    def __str__(self):
        return self.name

    def save(self, *args, **kwargs):
        super().save()
        # auto-evaluate type:
        if not self.origin:
            self.origin = self.ORIGIN
            self.save(*args, **kwargs)

    @property
    def groups(self):
        """
        Returns unique groups for the badge template.
        """

        return self.requirements.values_list("blend", flat=True).distinct()

    @classmethod
    def by_uuid(cls, template_uuid):
        """
        Returns badge template by UUID.
        """

        return cls.objects.filter(uuid=template_uuid, origin=cls.ORIGIN).first()

    def user_progress(self, username: str) -> float:
        """
        Determines a completion progress for user.
        """
        progress = BadgeProgress.for_user(username=username, template_id=self.id)
        return progress.ratio

    def is_completed(self, username: str) -> bool:
        """
        Checks if user has completed this badge template.
        """
        return self.user_progress(username) == 1.00


class CredlyBadgeTemplate(BadgeTemplate):
    """
    Credly badge template credential.

    Credly badge templates should not be created manually, instead they are pulled from the Credly Organization (API).
    Before being processed badge template must be activated.
    Before activation badge template must be configured (requirements and optional penalties).
    """

    ORIGIN = "credly"

    organization = models.ForeignKey(
        CredlyOrganization,
        on_delete=models.CASCADE,
        help_text=_("Credly Organization - template owner."),
    )

    @property
    def management_url(self):
        """
        Build external Credly dashboard URL.
        """
        credly_host_base_url = get_credly_base_url(settings)
        return f"{credly_host_base_url}mgmt/organizations/{self.organization.uuid}/badges/templates/{self.uuid}/details"


class BadgeRequirement(models.Model):
    """
    Describes what must happen for badge template to progress.

    - what unique event is expected to happen;
    - what exact conditions the expected event must carry in its payload;

    NOTE:   all attached to a badge template requirements must be fulfilled by default;
            to achieve "OR" processing logic for 2 attached requirements just group them (put identical group ID).
    """

    EVENT_TYPES = Choices(*settings.BADGES_CONFIG["events"])

    template = models.ForeignKey(
        BadgeTemplate,
        on_delete=models.CASCADE,
        related_name="requirements",
        help_text=_("Badge template this requirement serves for."),
    )
    event_type = models.CharField(
        max_length=255,
        choices=EVENT_TYPES,
        help_text=_(
            'Public signal type. Available events are configured in "BADGES_CONFIG" setting. '
            "The crucial aspect for event to carry UserData in its payload."
        ),
    )
    description = models.TextField(null=True, blank=True, help_text=_("Provide more details if needed."))
    blend = models.CharField(
        max_length=255,
        null=True,
        blank=True,
        help_text=_(
            "Optional. Group requirements together using the same Group ID for interchangeable (OR processing logic)."
        ),
        verbose_name=_("group"),
    )

    def __str__(self):
        return f"BadgeRequirement:{self.id}:{self.template.uuid}"

    def fulfill(self, username: str):
        """
        Marks itself as "done" for the user.

        Side effects:
            - notifies about a progression if any;

        Returns: (bool) if progression happened
        """
        template_id = self.template.id
        progress = BadgeProgress.for_user(username=username, template_id=template_id)
        fulfillment, created = Fulfillment.objects.get_or_create(progress=progress, requirement=self, blend=self.blend)

        if created:
            notify_requirement_fulfilled(
                sender=self,
                username=username,
                badge_template_id=template_id,
                fulfillment_id=fulfillment.id,
            )
        return created

    def reset(self, username: str):
        """
        Marks itself as "undone" for the user.

        - removes user progress for the requirement if any;
        - notifies about the regression if any;

        Returns: (bool) if any progress existed.
        """
        template_id = self.template.id
        fulfillment = Fulfillment.objects.filter(
            requirement=self,
            progress__username=username,
        ).first()
        deleted, __ = fulfillment.delete() if fulfillment else (False, 0)
        if deleted:
            notify_requirement_regressed(
                sender=self,
                username=username,
                badge_template_id=template_id,
            )
        return bool(deleted)

    def is_fulfilled(self, username: str) -> bool:
        """
        Checks if the requirement is fulfilled for the user.
        """

        return self.fulfillments.filter(progress__username=username, progress__template=self.template).exists()

    @classmethod
    def is_group_fulfilled(cls, *, group: str, template: BadgeTemplate, username: str) -> bool:
        """
        Checks if the group is fulfilled.
        """

        progress = BadgeProgress.for_user(username=username, template_id=template.id)
        requirements = cls.objects.filter(template=template, blend=group)
        fulfilled_requirements = requirements.filter(fulfillments__progress=progress).count()

        return fulfilled_requirements > 0

    def apply_rules(self, data: dict) -> bool:
        """
        Evaluates payload rules.
        """

        return all(rule.apply(data) for rule in self.rules.all()) if self.rules.exists() else False

    @property
    def is_active(self):
        """
        Checks if the requirement is active.
        """

        return self.template.is_active


class AbstractDataRule(models.Model):
    """
    Abstract DataRule configuration model.

    .. no_req_or_pen: This model has no requirement or penalty.
    """

    OPERATORS = Choices(
        ("eq", "="),
        ("ne", "!="),
        # ('lt', '<'),
        # ('gt', '>'),
    )

    TRUE_VALUES = ["True", "true", "Yes", "yes", "+"]
    FALSE_VALUES = ["False", "false", "No", "no", "-"]
    BOOL_VALUES = TRUE_VALUES + FALSE_VALUES

    data_path = models.CharField(
        max_length=255,
        help_text=_('Public signal\'s data payload nested property path, e.g: "user.pii.username".'),
        verbose_name=_("key path"),
    )
    operator = models.CharField(
        max_length=32,
        choices=OPERATORS,
        default=OPERATORS.eq,
        help_text=_("Expected value comparison operator. https://docs.python.org/3/library/operator.html"),
    )
    value = models.CharField(
        max_length=255,
        help_text=_('Expected value for the nested property, e.g: "cucumber1997".'),
        verbose_name=_("expected value"),
    )

    class Meta:
        abstract = True

    def apply(self, data: dict) -> bool:
        """
        Evaluates itself on the input data (event payload).

        This method retrieves a value specified by a data path within a given dictionary,
        converts that value to a string, and then applies a comparison operation against
        a predefined value. The comparison operation is determined by the `self.operator`
        attribute, which should match the name of an operator function in the `operator`
        module.

        Parameters:
        - data (dict):  A dictionary containing data against which the comparison operation
                        will be applied. The specific value to be compared is determined by
                        the `self.data_path` attribute, which specifies the path to the value
                        within the dictionary.

        Returns:
        - bool: True if the rule "worked".

        Example:
        Assuming `self.operator` is set to "eq", `self.data_path` is set to "user.age",
        and `self.value` is "30", then calling `apply({"user": {"age": 30}})` will return True
        because the age matches the specified value.
        """

        comparison_func = getattr(operator, self.operator, None)

        if comparison_func:
            data_value = str(keypath(data, self.data_path))
            return comparison_func(data_value, self._value_to_bool())
        return False

    def _value_to_bool(self):
        """
        Converts the value to a boolean or returns the original value if it is not a boolean string.
        """

        if self.value in self.TRUE_VALUES:
            return "True"
        if self.value in self.FALSE_VALUES:
            return "False"
        return self.value


class DataRule(AbstractDataRule):
    """
    Specifies expected data attribute value for event payload.
    NOTE: all data rules for a single requirement follow "AND" processing logic.
    """

    requirement = models.ForeignKey(
        BadgeRequirement,
        on_delete=models.CASCADE,
        help_text=_("Parent requirement for this data rule."),
        related_name="rules",
    )

    class Meta:
        unique_together = ("requirement", "data_path", "operator", "value")

    def __str__(self):
        return f"{self.requirement.template.uuid}:{self.data_path}:{self.operator}:{self.value}"

    @property
    def is_active(self):
        """
        Checks if the rule is active.
        """

        return self.requirement.template.is_active


class BadgePenalty(models.Model):
    """
    Describes badge regression rules for particular BadgeRequirement.
    """

    EVENT_TYPES = Choices(*settings.BADGES_CONFIG["events"])

    template = models.ForeignKey(
        BadgeTemplate,
        on_delete=models.CASCADE,
        help_text=_("Badge template this penalty serves for."),
    )
    event_type = models.CharField(
        max_length=255,
        choices=EVENT_TYPES,
        help_text=_(
            'Public signal type. Use namespaced types, e.g: "org.openedx.learning.student.registration.completed.v1"'
        ),
    )
    requirements = models.ManyToManyField(
        BadgeRequirement,
        help_text=_("Badge requirements for which this penalty is defined."),
    )

    class Meta:
        verbose_name_plural = _("Badge penalties")

    def __str__(self):
        return f"BadgePenalty:{self.id}:{self.template.uuid}"

    def apply_rules(self, data: dict) -> bool:
        """
        Evaluates payload rules.
        """

        return all(rule.apply(data) for rule in self.rules.all()) if self.rules.exists() else False

    def reset_requirements(self, username: str):
        """
        Resets all related requirements for the user.
        """

        for requirement in self.requirements.all():
            requirement.reset(username)

    @property
    def is_active(self):
        """
        Checks if the penalty is active.
        """

        return self.template.is_active


class PenaltyDataRule(AbstractDataRule):
    """
    Specifies expected data attribute value for penalty rule.
    NOTE: all data rules for a single penalty follow "AND" processing logic.
    """

    penalty = models.ForeignKey(
        BadgePenalty,
        on_delete=models.CASCADE,
        help_text=_("Parent penalty for this data rule."),
        related_name="rules",
    )

    class Meta:
        unique_together = ("penalty", "data_path", "operator", "value")

    def __str__(self):
        return f"{self.penalty.template.uuid}:{self.data_path}:{self.operator}:{self.value}"

    @property
    def is_active(self):
        """
        Checks if the rule is active.
        """

        return self.penalty.template.is_active


class BadgeProgress(models.Model):
    """
    Tracks a single badge template progress for user.

    - allows multiple requirements status tracking;
    - user-centric;
    """

    username = models.CharField(max_length=255)  # index
    template = models.ForeignKey(
        BadgeTemplate,
        models.SET_NULL,
        blank=True,
        null=True,
    )

    class Meta:
        verbose_name_plural = _("badge progress records")

    def __str__(self):
        return f"BadgeProgress:{self.username}"

    @classmethod
    def for_user(cls, *, username, template_id):
        """
        Service shortcut.
        """

        progress, __ = cls.objects.get_or_create(username=username, template_id=template_id)
        return progress

    @property
    def ratio(self) -> float:
        """
        Calculates badge template progress ratio.
        """

        if not self.groups:
            return 0.00

        true_values = len(list(filter(lambda x: x, self.groups.values())))
        return round(true_values / len(self.groups.keys()), 2)

    @property
    def groups(self):
        """
        Returns gorups and their statuses (fulfilled or not).
        """

        return {
            group: BadgeRequirement.is_group_fulfilled(group=group, template=self.template, username=self.username)
            for group in self.template.groups
        }

    @property
    def completed(self):
        """
        Checks if the badge template is completed.
        """

        return self.ratio == 1.00

    def progress(self):
        """
        Notify about the progress.
        """

        notify_progress_complete(self, self.username, self.template.id)

    def regress(self):
        """
        Notify about the regression.
        """

        notify_progress_incomplete(self, self.username, self.template.id)

    def reset(self):
        """
        Resets the progress.
        """

        Fulfillment.objects.filter(progress=self).delete()


class Fulfillment(models.Model):
    """
    Tracks completed badge template requirement for user.
    """

    progress = models.ForeignKey(BadgeProgress, on_delete=models.CASCADE)
    requirement = models.ForeignKey(
        BadgeRequirement,
        models.SET_NULL,
        blank=True,
        null=True,
        related_name="fulfillments",
    )
    blend = models.CharField(
        max_length=255,
        null=True,
        blank=True,
        help_text=_("Group ID for the requirement."),
        verbose_name=_("group"),
    )


class CredlyBadge(UserCredential):
    """
    Earned Credly badge (Badge template credential) for user.

    - tracks distributed (external Credly service) state for Credly badge.
    """

    STATES = Choices(
        "created",
        "no_response",
        "error",
        "pending",
        "accepted",
        "rejected",
        "revoked",
        "expired",
    )
    ISSUING_STATES = {
        STATES.pending,
        STATES.accepted,
        STATES.rejected,
    }

    state = StatusField(
        choices_name="STATES",
        help_text=_("Credly badge issuing state"),
        default=STATES.created,
    )

    external_uuid = models.UUIDField(
        blank=True,
        null=True,
        unique=True,
        help_text=_("Credly service badge identifier"),
    )

    def as_badge_data(self) -> BadgeData:
        """
        Represents itself as a BadgeData instance.
        """

        user = get_user_by_username(self.username)
        badge_template = self.credential

        badge_data = BadgeData(
            uuid=str(self.uuid),
            user=UserData(
                pii=UserPersonalData(
                    username=self.username,
                    email=user.email,
                    name=user.get_full_name(),
                ),
                id=user.lms_user_id,
                is_active=user.is_active,
            ),
            template=BadgeTemplateData(
                uuid=str(badge_template.uuid),
                origin=badge_template.origin,
                name=badge_template.name,
                description=badge_template.description,
                image_url=str(badge_template.icon),
            ),
        )

        return badge_data

    @property
    def propagated(self):
        """
        Checks if this user credential already has issued (external) Credly badge.
        """

        return self.external_uuid and (self.state in self.ISSUING_STATES)
