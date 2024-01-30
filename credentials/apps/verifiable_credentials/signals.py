"""
Verifiable Credentials signal handlers.
"""

from django.db.models.signals import post_save
from django.dispatch import receiver

from credentials.apps.credentials.models import UserCredential

from .issuance.models import IssuanceLine


@receiver(post_save, sender=UserCredential)
def update_issuance_lines(instance, created, **kwargs):
    """
    Keep track on user credential status and update related issuance lines.add()

    NOTE:
        currently, it syncronize any change, but in the future we may want to "freeze" status for once
        revoked credentials.
    """
    user_credential = instance

    # there are no verifiable credentials yet for a newly created user credential:
    if created:
        return

    # find all related issuance lines and switch status:
    issuance_lines = IssuanceLine.objects.filter(user_credential=user_credential)
    issuance_lines.update(status=user_credential.status)
