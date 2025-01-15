from datetime import datetime

import attr


@attr.s(auto_attribs=True, frozen=True)
class AccredibleRecipient:
    """
    Represents the recipient data in the credential.

    Attributes:
        name (str): The recipient's name.
        email (str): The recipient's email address.
    """

    name: str
    email: str


@attr.s(auto_attribs=True, frozen=True)
class AccredibleCredential:
    """
    Represents the credential data.

    Attributes:
        recipient (RecipientData): Information about the recipient.
        group_id (int): ID of the credential group.
        name (str): Title of the credential.
        issued_on (datetime): Date when the credential was issued.
        complete (bool): Whether the credential process is complete.
    """

    recipient: AccredibleRecipient
    group_id: int
    name: str
    issued_on: datetime
    complete: bool


@attr.s(auto_attribs=True, frozen=True)
class AccredibleExpiredCredential:
    """
    Represents the data required to expire a credential.
    """

    expired_on: datetime


@attr.s(auto_attribs=True, frozen=True)
class AccredibleBadgeData:
    """
    Represents the data required to issue a badge.
    """

    credential: AccredibleCredential


@attr.s(auto_attribs=True, frozen=True)
class AccredibleExpireBadgeData:
    """
    Represents the data required to expire a badge.
    """

    credential: AccredibleExpiredCredential
