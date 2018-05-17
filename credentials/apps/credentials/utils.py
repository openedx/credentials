from itertools import groupby


def to_language(locale):
    if locale is None:
        return None
    # Convert to bytes to get ascii-lowercasing, to avoid the Turkish I problem.
    return locale.replace('_', '-').encode().lower().decode()


def validate_duplicate_attributes(attributes):
    """
    Validate the attributes data

    Arguments:
        attributes (list): List of dicts contains attributes data

    Returns:
        Boolean: Return True only if data has no duplicated namespace and name

    """

    def keyfunc(attribute):
        return attribute['name']

    sorted_data = sorted(attributes, key=keyfunc)
    for __, group in groupby(sorted_data, key=keyfunc):
        if len(list(group)) > 1:
            return False
    return True
