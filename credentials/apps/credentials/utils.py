"""
Helper methods for data validation.
"""
from itertools import groupby


def validate_duplicate_attributes(attributes):
    """
    Validate the attributes data

    Arguments:
            attributes (list): List of dicts contains attributes data.

    Returns:
        Boolean: Return True if data has no duplicate names otherwise False

    """
    def keyfunc(attribute):  # pylint: disable=missing-docstring
        return attribute['name']

    sorted_data = sorted(attributes, key=keyfunc)
    for __, group in groupby(sorted_data, key=keyfunc):
        if len(list(group)) > 1:
            return False
    return True
