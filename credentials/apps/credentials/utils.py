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
        Boolean: Return True if data has no duplicated namespace and name otherwise False

    """
    for __, group in groupby(sorted(attributes), lambda x: (x['namespace'], x['name'])):
        if len(list(group)) > 1:
            return False
    return True
