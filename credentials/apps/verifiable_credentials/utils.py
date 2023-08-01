import base64
from io import BytesIO
from uuid import UUID

import qrcode
from django.contrib.contenttypes.models import ContentType

from credentials.apps.credentials.api import get_user_credentials_by_content_type
from credentials.apps.credentials.data import UserCredentialStatus


def get_user_program_credentials_data(username):
    """
    Translates a list of UserCredentials (for programs) into context data.

    Arguments:
        request_username(str): Username for whom we are getting UserCredential objects for

    Returns:
        list(dict): A list of dictionaries, each dictionary containing information for a credential that the
        user awarded
    """
    program_cert_content_type = ContentType.objects.get(app_label="credentials", model="programcertificate")
    program_credentials = get_user_credentials_by_content_type(
        username, [program_cert_content_type], UserCredentialStatus.AWARDED.value
    )
    return [
        {
            "uuid": credential.uuid.hex,
            "status": credential.status,
            "username": credential.username,
            "download_url": credential.download_url,
            "credential_id": credential.credential_id,
            "program_uuid": credential.credential.program_uuid.hex,
            "program_title": credential.credential.program.title,
            "program_org": ", ".join(
                credential.credential.program.authoring_organizations.values_list("name", flat=True)
            ),
            "modified_date": credential.modified.date().isoformat(),
        }
        for credential in program_credentials
    ]


def generate_base64_qr_code(text):
    qr = qrcode.QRCode(error_correction=qrcode.constants.ERROR_CORRECT_L, box_size=10)
    qr.add_data(text)
    qr.make(fit=True)

    img = qr.make_image()
    buffered = BytesIO()
    img.save(buffered, format="PNG")
    img_str = base64.b64encode(buffered.getvalue()).decode("utf-8")
    return img_str


def is_valid_uuid(uuid_to_test, version=4):
    """
    Check if uuid_to_test is a valid UUID.

    Parameters
    ----------
    uuid_to_test : str
    version : {1, 2, 3, 4}

    Returns
    -------
    `True` if uuid_to_test is a valid UUID, otherwise `False`.

    Examples
    --------
    >>> is_valid_uuid('c9bf9e57-1685-4c89-bafb-ff5af830be8a')
    True
    >>> is_valid_uuid('c9bf9e58')
    False
    """

    try:
        UUID(uuid_to_test, version=version)
        return True
    except (ValueError, TypeError):
        return False


def capitalize_first(wording):
    """
    Unlike the standard string.capitalize() do not touches anything besides the initial character.
    """
    if not isinstance(wording, str):
        return wording
    return f"{wording[:1].upper()}{wording[1:]}"
