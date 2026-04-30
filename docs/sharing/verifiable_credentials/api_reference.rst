.. _vc-api-reference:

API Reference
=============

All endpoints are prefixed with ``/verifiable_credentials/api/v1/``.

.. _vc-api-credentials-list:

GET /credentials/
-----------------

List all credentials issued to the authenticated user. Supports filtering by credential type.

**Authentication:** JWT or Session (required)

**Query parameters:**

.. list-table::
   :header-rows: 1
   :widths: 20 15 65

   * - Parameter
     - Type
     - Description
   * - ``types``
     - string
     - Comma-separated credential types to filter. Valid values: ``programcertificate``, ``coursecertificate``.
       Omit to return all types.

**Example request:**

.. code-block:: sh

    GET /verifiable_credentials/api/v1/credentials/?types=coursecertificate,programcertificate

**Example response:**

.. code-block:: json

    {
        "program_credentials": [
            {
                "uuid": "4a665745d1ba4dfd8f54b58e822b6585",
                "status": "awarded",
                "username": "staff",
                "credential_id": 1,
                "credential_uuid": "525756b010aa4c788881141acca72538",
                "credential_title": "Title of a program",
                "credential_org": "",
                "modified_date": "2024-12-18"
            }
        ],
        "course_credentials": [
            {
                "uuid": "5135e99ef1d14bca9135972270ef887b",
                "status": "awarded",
                "username": "staff",
                "credential_id": 1,
                "credential_uuid": "course-v1:rg+program_course+2024",
                "credential_title": "Course cert configuration",
                "credential_org": "rg",
                "modified_date": "2024-12-18"
            }
        ]
    }

.. _vc-api-credentials-init:

POST /credentials/init/
-----------------------

Initialize a verifiable credential issuance. Creates an ``IssuanceLine`` and returns a deeplink and QR code for the
learner to complete the flow with their wallet app.

**Authentication:** JWT or Session (required)

**Request body:**

.. list-table::
   :header-rows: 1
   :widths: 25 15 60

   * - Field
     - Type
     - Description
   * - ``credential_uuid``
     - string (UUID)
     - The ``UserCredential`` UUID to issue a VC for. Required.
   * - ``storage_id``
     - string
     - The storage backend (wallet) identifier. Required.

**Example response:**

.. code-block:: json

    {
        "deeplink": "dccrequest://request?issuer=did:key:z6Mk...&vc_request_url=...&auth_type=bearer&challenge=...&vp_version=1.1",
        "qrcode": "<base64-encoded PNG>",
        "app_link_android": "https://play.google.com/store/apps/details?id=...",
        "app_link_ios": "https://apps.apple.com/app/..."
    }

The response includes ``app_link_android`` and ``app_link_ios`` for mobile storage backends, or ``"redirect": true``
for web-based storage backends.

.. _vc-api-credentials-issue:

POST /credentials/issue/<uuid>/
-------------------------------

Issue a verifiable credential for the given ``IssuanceLine``. The wallet app calls this endpoint after receiving the
deeplink.

**Authentication:** JWT or Session, **or** a Verifiable Presentation (VP) with ``proofPurpose: "authentication"``
and a ``challenge`` matching the ``IssuanceLine`` UUID.

**Returns:** A signed verifiable credential (``201 Created``).

.. _vc-api-storages:

GET /storages/
--------------

List all available storage backends (digital wallets).

**Authentication:** JWT or Session (required)

**Example response:**

.. code-block:: json

    [
        {
            "id": "credentials.apps.verifiable_credentials.storages.learner_credential_wallet.LCWallet",
            "name": "Learner Credential Wallet"
        }
    ]

.. _vc-api-status-list:

GET /status-list/2021/v1/<issuer_id>/
-------------------------------------

Retrieve the Status List 2021 credential for a given issuer. Relying parties use this endpoint to verify whether a
credential has been revoked.

**Authentication:** None (public endpoint, ``AllowAny``).

**Path parameters:**

.. list-table::
   :header-rows: 1
   :widths: 20 15 65

   * - Parameter
     - Type
     - Description
   * - ``issuer_id``
     - string
     - The issuer's decentralized identifier (DID), e.g. ``did:key:z6Mk...``

**Returns:** A signed Status List 2021 verifiable credential. See :ref:`vc-status-list-api` for the full response
structure.
