import attr
import inspect

from attrs import asdict
from django.conf import settings
from openedx_events.learning.data import UserData
from openedx_events.tooling import OpenEdxPublicSignal


def get_badging_event_types():
    """
    Figures out which events are available for badges.
    """
    return settings.BADGES_CONFIG.get("events", [])


def credly_check():
    """
    Checks if Credly is configured.
    """

    credly_settings = settings.BADGES_CONFIG.get("credly", None)
    if credly_settings is None:
        return False
    keys = (
        "CREDLY_BASE_URL",
        "CREDLY_API_BASE_URL",
        "CREDLY_SANDBOX_BASE_URL",
        "CREDLY_SANDBOX_API_BASE_URL",
        "USE_SANDBOX",
    )
    return all([key in credly_settings.keys() for key in keys])


def keypath(payload, keys_path):
    """
    Retrieve the value from a nested dictionary using a dot-separated key path.

    Traverses a nested dictionary `payload` to find the value specified by the dot-separated
    key path `keys_path`. Each key in `keys_path` represents a level in the nested dictionary.

    Parameters:
    - payload (dict): The nested dictionary to search.
    - keys_path (str): The dot-separated path of keys to traverse in the dictionary.

    Returns:
        - The value found at the specified key path in the dictionary, or None if any key in the path
        does not exist or the traversal leads to a non-dictionary object before reaching the final key.

    Example:
    >>> payload = {'a': {'b': {'c': 1}}}
    >>> keypath(payload, 'a.b.c')
    1
    >>> keypath(payload, 'a.b.d')
    None
    """

    keys = keys_path.split(".")
    current = payload

    def traverse(current, keys):
        """
        Recursive function to traverse the dictionary.
        """

        if not keys:
            return current
        key = keys[0]
        if attr.has(current):
            current = asdict(current)
        if isinstance(current, dict) and key in current:
            return traverse(current[key], keys[1:])
        else:
            return None

    return traverse(current, keys)


def get_user_data(data: attr.s) -> UserData:
    """
    Extracts UserData object from any dataclass that contains UserData as a field.

    Parameters:
        - data: Input dict that contains attr class, which has UserData somewhere deep.

    Returns:
        UserData: UserData object contained within the input dataclass.
    """

    if isinstance(data, UserData):
        return data

    for _, attr_value in inspect.getmembers(data):
        if isinstance(attr_value, UserData):
            return attr_value
        elif attr.has(attr_value):
            user_data = get_user_data(attr_value)
            if user_data:
                return user_data
    return None


def extract_payload(public_signal_kwargs: dict) -> attr.s:
    """
    Extracts the event payload from the event data.

    Parameters:
        - public_signal_kwargs: The event data.

    Returns:
        attr.s: The extracted event payload.
    """
    for value in public_signal_kwargs.values():
        if attr.has(value):
            return value


def get_event_type_data(event_type: str) -> attr.s:
    """
    Extracts the dataclass for a given event type.

    Parameters:
        - event_type: The event type to extract dataclass for.

    Returns:
        attr.s: The dataclass for the given event type.
    """

    signal = OpenEdxPublicSignal.get_signal_by_type(event_type)
    return extract_payload(signal.init_data)


def get_event_type_keypaths(event_type: str) -> list:
    """
    Extracts all possible keypaths for a given event type.

    Parameters:
        - event_type: The event type to extract keypaths for.

    Returns:
        list: A list of all possible keypaths for the given event type.
    """

    data = get_event_type_data(event_type)

    def get_data_keypaths(data):
        """
        Extracts all possible keypaths for a given dataclass.
        """

        keypaths = []
        for field in attr.fields(data):
            if attr.has(field.type):
                keypaths += [
                    f"{field.name}.{keypath}"
                    for keypath in get_data_keypaths(field.type)
                ]
            else:
                keypaths.append(field.name)
        return keypaths

    keypaths = []
    for field in attr.fields(data):
        if attr.has(field.type):
            keypaths += [
                f"{field.name}.{keypath}"
                for keypath in get_data_keypaths(field.type)
                if f"{field.name}.{keypath}"
                not in settings.BADGES_CONFIG.get("rules", {}).get("ignored_keypaths", [])
            ]
        else:
            keypaths.append(field.name)
    return keypaths


def get_event_type_attr_type_by_keypath(event_type: str, keypath: str):
    """
    Extracts the attribute type for a given keypath in the event type.

    Parameters:
        - event_type: The event type to extract dataclass for.
        - keypath: The keypath to extract attribute type for.

    Returns:
        type: The attribute type for the given keypath in the event data.
    """

    data = get_event_type_data(event_type)
    data_attrs = attr.fields(data)

    def get_attr_type_by_keypath(data_attrs, keypath):
        """
        Extracts the attribute type for a given keypath in the dataclass.
        """

        keypath_parts = keypath.split(".")
        for attr_ in data_attrs:
            if attr_.name == keypath_parts[0]:
                if len(keypath_parts) == 1:
                    return attr_.type
                elif attr.has(attr_.type):
                    return get_attr_type_by_keypath(attr.fields(attr_.type), ".".join(keypath_parts[1:]))
        return None
    
    return get_attr_type_by_keypath(data_attrs, keypath)
