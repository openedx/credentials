"""
Storages utils.
"""

from ..settings import vc_settings


def get_available_storages():
    """
    Returns available for users verifiable credentials storages.
    """
    return vc_settings.DEFAULT_STORAGES


def get_storages():
    """
    Returns all verifiable credentials storages.
    """
    return get_available_storages() + [
        vc_settings.STATUS_LIST_STORAGE,
    ]


def get_storage(storage_id):
    for storage in get_storages():
        if storage.ID == storage_id:
            return storage

    return None
