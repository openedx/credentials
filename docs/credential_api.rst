Credential APIs
===============

The following APIs are available for creating a user credential or updating the
status for an existing user credential.

+----------------------------------------+--------+---------------------------------+
| Task                                   | Method | Endpoint                        |
+========================================+========+=================================+
| Create a user credential for a program | POST   |  /api/v1/user_credentials/      |
+----------------------------------------+--------+---------------------------------+
| Update the status of a user credential | PATCH  |  /api/v1/user_credentials/:id   |
+----------------------------------------+--------+---------------------------------+

Create a User Credential for a Program
--------------------------------------

To create a user credential for a program, use ``user_credentials``.

**Example Request**

.. code-block::

    url: /api/v1/user_credentials/:id
    Content-Type: application/json
    Method: POST

    {
        "username": "test-user",
        "credential": {
            "program_id": 100
        },
        "status": "awarded"
        "attributes": [
            {
                "namespace": "whitelist",
                "name": "Whitelist",
                "value": "Your reason for whitelisting."
            },
            {
                "namespace": "grade",
                "name": "Final Grade",
                "value": "0.85"
            }
        ]
    }

**Note:**

* The ``username``, ``credential``, and ``status`` parameters are required.
* The ``attributes`` parameter is optional.
* If you use the ``whitelist`` or ``grade`` attributes, you can only change the ``value``
  parameter. 
* If you send a program-based user credential request, you can only provide the
  ``whitelist`` attribute.

Update the Status of a User Credential
--------------------------------------

To update the status of a user credential, use ``status``.

**Example Request**

.. code-block::

    url: /api/v1/user_credentials/:id
    Content-Type: application/json
    Method: PATCH

    {
        "status": "REVOKED"
    }

**Note:**

* This endpoint only accepts the ``status`` parameter. Valid values for the status
  parameter are ``AWARDED`` and ``REVOKED``.
