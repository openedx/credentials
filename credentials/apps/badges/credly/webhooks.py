import logging

from django.contrib.sites.shortcuts import get_current_site
from django.shortcuts import get_object_or_404
from rest_framework import status
from rest_framework.response import Response
from rest_framework.views import APIView

from ..models import CredlyBadgeTemplate, CredlyOrganization
from .api_client import CredlyAPIClient


logger = logging.getLogger(__name__)


class CredlyWebhook(APIView):
    """
    Public API (webhook endpoint) to handle incoming Credly updates.

    Usage:
        POST <credentials>/credly-badges/api/webhook/
    """

    authentication_classes = []
    permission_classes = []

    def post(self, request):
        """
        Handle incoming update events from the Credly service.

        https://sandbox.credly.com/docs/webhooks#requirements

        Handled events:
            - badge_template.created
            - badge_template.changed
            - badge_template.deleted

        - tries to recognize Credly Organization context;
        - validates event type and its payload;
        - performs corresponding item (badge template) updates;

        Returned statuses:
            - 204
            - 404
        """
        credly_api_client = CredlyAPIClient(request.data.get("organization_id"))

        event_info_response = credly_api_client.fetch_event_information(request.data.get("id"))
        event_type = request.data.get("event_type")

        if event_type == "badge_template.created":
            self.handle_badge_template_created_event(request, event_info_response)
        elif event_type == "badge_template.changed":
            self.handle_badge_template_changed_event(request, event_info_response)
        elif event_type == "badge_template.deleted":
            self.handle_badge_template_deleted_event(request, event_info_response)
        else:
            logger.error(f"Unknown event type: {event_type}")

        return Response(status=status.HTTP_204_NO_CONTENT)

    @staticmethod
    def handle_badge_template_created_event(request, data):
        """
        Create a new badge template.
        """
        # TODO: dry it
        badge_template = data.get("data", {}).get("badge_template", {})
        owner = data.get("data", {}).get("badge_template", {}).get("owner", {})

        organization = get_object_or_404(CredlyOrganization, uuid=owner.get("id"))

        CredlyBadgeTemplate.objects.update_or_create(
            uuid=badge_template.get("id"),
            organization=organization,
            defaults={
                "site": get_current_site(request),
                "name": badge_template.get("name"),
                "state": badge_template.get("state"),
                "description": badge_template.get("description"),
                "icon": badge_template.get("image_url"),
            },
        )

    @staticmethod
    def handle_badge_template_changed_event(request, data):
        """
        Change the badge template.
        """
        # TODO: dry it
        badge_template = data.get("data", {}).get("badge_template", {})
        owner = data.get("data", {}).get("badge_template", {}).get("owner", {})

        organization = get_object_or_404(CredlyOrganization, uuid=owner.get("id"))

        CredlyBadgeTemplate.objects.update_or_create(
            uuid=badge_template.get("id"),
            organization=organization,
            defaults={
                "site": get_current_site(request),
                "name": badge_template.get("name"),
                "state": badge_template.get("state"),
                "description": badge_template.get("description"),
                "icon": badge_template.get("image_url"),
            },
        )

        if badge_template.get("state") != CredlyBadgeTemplate.STATES.active:
            CredlyBadgeTemplate.objects.filter(
                uuid=badge_template.get("id"),
                organization=organization,
            ).update(is_active=False)

    @staticmethod
    def handle_badge_template_deleted_event(request, data):
        """
        Deletes the badge template by provided uuid.
        """
        CredlyBadgeTemplate.objects.filter(
            uuid=data.get("data", {}).get("badge_template", {}).get("id"),
            site=get_current_site(request),
        ).delete()
