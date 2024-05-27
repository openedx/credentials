import uuid

from django import forms
from django.contrib.sites.models import Site
from django.test import TestCase
from django.utils.translation import gettext as _

from credentials.apps.badges.admin_forms import BadgePenaltyForm
from credentials.apps.badges.models import BadgeRequirement, BadgeTemplate


COURSE_PASSING_EVENT = "org.openedx.learning.course.passing.status.updated.v1"


class BadgePenaltyFormTestCase(TestCase):
    def setUp(self):
        self.site = Site.objects.create(domain="test_domain", name="test_name")
        self.badge_template1 = BadgeTemplate.objects.create(
            uuid=uuid.uuid4(), name="test_template", state="draft", site=self.site
        )
        self.badge_template2 = BadgeTemplate.objects.create(
            uuid=uuid.uuid4(), name="test_template", state="draft", site=self.site
        )
        self.requirement1 = BadgeRequirement.objects.create(
            template=self.badge_template1,
            event_type=COURSE_PASSING_EVENT,
            description="Test course passing award description 1",
        )
        self.requirement2 = BadgeRequirement.objects.create(
            template=self.badge_template2,
            event_type=COURSE_PASSING_EVENT,
            description="Test course passing award description 2",
        )
        self.requirement3 = BadgeRequirement.objects.create(
            template=self.badge_template2,
            event_type=COURSE_PASSING_EVENT,
            description="Test course passing award description 3",
        )

    def test_clean_requirements_same_template(self):
        form = BadgePenaltyForm()
        form.cleaned_data = {
            "template": self.badge_template2,
            "requirements": [
                self.requirement2,
                self.requirement3,
            ],
        }
        self.assertEqual(
            form.clean(),
            {
                "template": self.badge_template2,
                "requirements": [
                    self.requirement2,
                    self.requirement3,
                ],
            },
        )

    def test_clean_requirements_different_template(self):
        form = BadgePenaltyForm()
        form.cleaned_data = {
            "template": self.badge_template1,
            "requirements": [
                self.requirement2,
                self.requirement1,
            ],
        }

        with self.assertRaises(forms.ValidationError) as cm:
            form.clean()

        self.assertEqual(str(cm.exception), "['All requirements must belong to the same template.']")
