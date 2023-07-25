"""
Status List 2021 storage.
"""

from django.utils.translation import gettext as _

from ..settings import vc_settings
from . import BaseStorage


class StatusList2021(BaseStorage):
    """
    Status List 2021 storage.
    """

    ID = "vc_status_list_2021"
    NAME = _("Status List 2021")
    PREFERRED_DATA_MODEL = vc_settings.STATUS_LIST_DATA_MODEL
