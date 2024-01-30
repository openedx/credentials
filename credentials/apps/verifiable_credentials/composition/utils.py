"""
Composition utils.
"""

from ..settings import vc_settings


def get_available_data_models():
    """
    Return available for users verifiable credentials data models.
    """
    return vc_settings.DEFAULT_DATA_MODELS


def get_data_models():
    """
    Return configured verifiable credentials data models.
    """
    return get_available_data_models() + [
        vc_settings.STATUS_LIST_DATA_MODEL,
    ]


def get_data_model(model_id):
    """
    Return a data model by its ID from the currently available list.
    """
    for data_model in get_data_models():
        if data_model.ID == model_id:
            return data_model

    return None
