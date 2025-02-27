"""
Public data structures for this app.

This should only ever be consumed and should never import anything other than
stdlib modules, so that it may be consumed everywhere.
"""

from dataclasses import dataclass
from enum import Enum


# Currently using a dataclass version of the legacy namedtuples so the consuming
# app can mutate them for their needs. Future version should use frozen
# dataclasses and consuming app can create their own internal structures using
# the values from the frozen data rather than dataclass with too many
# requirements.
@dataclass
class OrganizationDetails:
    uuid: str
    key: str
    name: str
    display_name: str
    certificate_logo_image_url: str


# See comment above OrganizationDetails
@dataclass
class ProgramDetails:
    uuid: str
    title: str
    type: str
    type_slug: str
    credential_title: str
    course_count: int
    organizations: list
    hours_of_effort: int
    status: str


class ProgramStatus(Enum):
    ACTIVE = "active"
    RETIRED = "retired"
    DELETED = "deleted"
    UNPUBLISHED = "unpublished"


class PathwayStatus(Enum):
    RETIRED = "retired"
    UNPUBLISHED = "unpublished"
    PUBLISHED = "published"
