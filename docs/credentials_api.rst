Credentials API
===============

The ``credentials`` resource should be used for all API calls.

+----------------------------------------+--------+---------------------------------+
| Task                                   | Method | Endpoint                        |
+========================================+========+=================================+
| Get a list of credentials              | GET    |  /api/v2/credentials/           |
+----------------------------------------+--------+---------------------------------+
| Get a specific credential              | GET    |  /api/v2/credentials/:uuid      |
+----------------------------------------+--------+---------------------------------+
| Create a new credential                | POST   |  /api/v2/credentials/           |
+----------------------------------------+--------+---------------------------------+
| Update a credential                    | PATCH  |  /api/v2/credentials/:uuid      |
+----------------------------------------+--------+---------------------------------+


Create a New Credential
-----------------------
**Example Request**

.. code-block:: text

    POST /api/v2/credentials/

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
* When creating a user credential for a program, the API also checks to see if an updated email needs to be sent to a credit pathway.  For more information, please consult the Credit Pathways doc.


Update a Credential
-------------------

The default value of ``status`` parameter for a user credential is ``awarded``.
To update the status of a user credential, use ``status``.

**Example Request**

.. code-block:: text

    PATCH /api/v2/credentials/:uuid

    {
        "status": "revoked"
    }

**Note:**

* This endpoint only accepts the ``status`` parameter. Valid values for the status
  parameter are ``awarded`` and ``revoked``.


Retrieve a Credential
---------------------

To get information about a specific credential for a single user, use the credential ``uuid``.

**Example Request**

.. code-block:: text

    GET /api/v2/credentials/a2810ab0-c084-43de-a9db-fa484fcc82bc

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

All credentials are returned by default for any user with the `credentials.view_credential` permission.


Get a List of All Credentials for a User
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

To get a list of all credentials that a user has earned, use ``credentials``.
You must include the ``username`` parameter in the query string.

This endpoint does not allow you to get a list of all credentials for all users.
You can filter the returned list of credentials by using the ``username``
or ``status`` parameters in the query string.

**Example Requests**

.. code-block:: text

    GET api/v2/credentials/?username=<username>
    GET api/v2/credentials/?username=<username>&status=<status>

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
Only users with the `credentials.view_credential` permission, or credential awardees, can filter by username.


Get a List of All Credentials for a Program
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

You can filter the returned list of credentials by using the ``program_uuid`` parameter in the query string.

**Example Requests**

.. code-block:: text

    GET api/v1/credentials/?program_uuid=<program_uuid>

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
        ]
    }
