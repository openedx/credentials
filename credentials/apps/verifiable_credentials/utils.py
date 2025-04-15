import base64
from io import BytesIO
from uuid import UUID

import qrcode
from django.contrib.contenttypes.models import ContentType

from credentials.apps.catalog.models import CourseRun
from credentials.apps.credentials.api import get_user_credentials_by_content_type
from credentials.apps.credentials.data import UserCredentialStatus


def get_user_credentials_data(username, model):
    """
    Translates a list of UserCredentials (for programs) into context data.

    Arguments:
        request_username(str): Username for whom we are getting UserCredential objects for
        model(str): The model for content type (programcertificate | coursecertificate)

    Returns:
        list(dict): A list of dictionaries, each dictionary containing information for a credential that the
        user awarded
    """
    try:
        credential_cert_content_type = ContentType.objects.get(app_label="credentials", model=model)
    except ContentType.DoesNotExist:
        return []

    credentials = get_user_credentials_by_content_type(
        username, [credential_cert_content_type], UserCredentialStatus.AWARDED.value
    )

    data = []
    for credential in credentials:
        if model == "programcertificate":
            credential_uuid = credential.credential.program_uuid.hex
            credential_title = credential.credential.program.title
            credential_org = ", ".join(
                credential.credential.program.authoring_organizations.values_list("name", flat=True)
            )
        elif model == "coursecertificate":
            course_run = CourseRun.objects.filter(key=credential.credential.course_id).first()
            course = getattr(course_run, "course", None)
            credential_uuid = credential.credential.course_id
            credential_title = credential.credential.title or getattr(course, "title", "")
            credential_org = credential.credential.course_key.org

        data.append(
            {
                "uuid": credential.uuid.hex,
                "status": credential.status,
                "username": credential.username,
                "credential_id": credential.credential_id,
                "credential_uuid": credential_uuid,  # pylint: disable=possibly-used-before-assignment
                "credential_title": credential_title,  # pylint: disable=possibly-used-before-assignment
                "credential_org": credential_org,  # pylint: disable=possibly-used-before-assignment
                "modified_date": credential.modified.date().isoformat(),
            }
        )

    return data


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
