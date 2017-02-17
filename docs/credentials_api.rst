Credential APIs
===============

The following APIs are available for creating a user credential or updating the
status for an existing user credential.

+----------------------------------------+--------+---------------------------------+
| Task                                   | Method | Endpoint                        |
+========================================+========+=================================+
| Create a user credential for a program | POST   |  /api/v2/credentials/      |
+----------------------------------------+--------+---------------------------------+
| Update the status of a user credential | PATCH  |  /api/v2/credentials/:uuid |
+----------------------------------------+--------+---------------------------------+

Create a User Credential for a Program
--------------------------------------

To create a user credential for a program, use ``credentials``.

**Example Request**

.. code-block:: json

    url: /api/v2/credentials/
    Content-Type: application/json
    Method: POST

    {
        "username": "test-user",
        "credential": {
            "program_uuid": "244af8cb-7cdd-487e-afc0-aa0b6391b1fd"
        },
        "attributes": [
            {
                "name": "whitelist_reason",
                "value": "Your reason for whitelisting."
            }
        ]
    }

**Note:**

* The ``username`` and ``credential`` parameters are required.
* The ``attributes`` parameter is optional.
* If you use the ``whitelist`` or ``grade`` attributes, you can only change the ``value``
  parameter. 
* If you send a program-based user credential request, you can only provide the
  ``whitelist`` attribute.

Update the Status of a User Credential
--------------------------------------

The default value of ``status`` parameter for a user credential is ``awarded``.
To update the status of a user credential, use ``status``.

**Example Request**

.. code-block:: json

    url: /api/v2/credentials/:uuid
    Content-Type: application/json
    Method: PATCH

    {
        "status": "revoked"
    }

**Note:**

* This endpoint only accepts the ``status`` parameter. Valid values for the status
  parameter are ``awarded`` and ``revoked``.


Credential APIs
===============

The following APIs are available for listing and filtering user credentials:

+--------------------------------------------------+--------+--------------------------------------+
| Task                                             | Method | Endpoint                             |
+==================================================+========+======================================+
| Get a specific credential for a single user      |  GET   |  /api/v2/credentials/:uuid      |
+==================================================+========+======================================+
| Get a list of all credentials  |  GET   |  /api/v2/credentials/           |
+--------------------------------------------------+--------+--------------------------------------+


Get a Specific Credential for a Single User
-------------------------------------------

To get information about a specific credential for a single user, use the credential ``uuid``.

**Example Request**

.. code-block:: bash

    /api/v2/credentials/a2810ab0-c084-43de-a9db-fa484fcc82bc

**Example Response**

.. code-block:: json

    {
        "username": "admin",
        "credential": {
            "credential_id": 1,
            "program_uuid": "244af8cb-7cdd-487e-afc0-aa0b6391b1fd"
        },
        "status": "revoked",
        "download_url": "www.example.com",
        "uuid": "a2810ab0-c084-43de-a9db-fa484fcc82bc",
        "attributes": [
            {
                "name": "whitelist_reason",
                "value": "Your reason for whitelisting."
            }
        ],
        "created": "2015-12-17T09:28:35.075376Z",
        "modified": "2016-01-02T12:58:15.744188Z",
        "certificate_url": "http://0.0.0.0:8004/credentials/a2810ab0c08443dea9dbfa484fcc82bc/"
    }


Get a List of Credentials
-------------------------

List endpoints are used to get a list of user, course, and program credentials.
All list endpoints show 20 records per page.


Get a List of All Credentials for a User
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

To get a list of all credentials that a user has earned, use ``credentials``.
You must include the ``username`` parameter in the query string.

This endpoint does not allow you to get a list of all credentials for all users.
You can filter the returned list of credentials by using the ``username``
or ``status`` parameters in the query string.

**Example Requests**

.. code-block:: bash

    api/v2/credentials/?username=<username>
    api/v2/credentials/?username=<username>&status=<status>

**Example Response**

.. code-block:: json

    {
        "count": 1,
        "next": null,
        "previous": null,
        "results": [
            {
                "username": "admin",
                "credential": {
                    "credential_id": 1,
                    "program_uuid": "244af8cb-7cdd-487e-afc0-aa0b6391b1fd"
                },
                "status": "revoked",
                "download_url": "www.example.com",
                "uuid": "a2810ab0-c084-43de-a9db-fa484fcc82bc",
                "attributes": [
                    {
                        "name": "whitelist_reason",
                        "value": "Your reason for whitelisting."
                    }
                ],
                "created": "2015-12-17T09:28:35.075376Z",
                "modified": "2016-01-02T12:58:15.744188Z",
                "certificate_url": "http://0.0.0.0:8004/credentials/a2810ab0c08443dea9dbfa484fcc82bc/"
            },
        ]
    }

**Note:**
If you do not include the ``username`` parameter, you receive the following
``status_code=400`` error message:

``A username query string parameter is required for filtering user credentials.``

Get a List of All Credentials for a Program
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

To get a list of all credentials that users have earned for a specific program, use the ``credentials`` endpoint.

You can filter the returned list of credentials by using the ``program_uuid`` parameter in the query string.

**Example Requests**

.. code-block:: bash

    api/v1/credentials/?program_uuid=<program_uuid>

**Example Response**

.. code-block:: json

    {
        "count": 4,
        "next": null,
        "previous": null,
        "results": [
            {
                "id": 1,
                "username": "admin",
                "credential": {
                    "credential_id": 1,
                    "program_id": 100
                },
                "status": "revoked",
                "download_url": "www.example.com",
                "uuid": "a2810ab0-c084-43de-a9db-fa484fcc82bc",
                "attributes": [
                    {
                        "name": "whitelist_reason",
                        "value": "Your reason for whitelisting."
                    }
                ],
                "created": "2015-12-17T09:28:35.075376Z",
                "modified": "2016-01-02T12:58:15.744188Z",
                "certificate_url": "http://0.0.0.0:8004/credentials/a2810ab0c08443dea9dbfa484fcc82bc/"
            }
        ]
    }
