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

.. code-block:: json

    url: /api/v1/user_credentials/
    Content-Type: application/json
    Method: POST

    {
        "username": "test-user",
        "credential": {
            "program_id": 100
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

    url: /api/v1/user_credentials/:id
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
| Get a specific credential for a single user      |  GET   |  /api/v1/user_credentials/:id        |
+--------------------------------------------------+--------+--------------------------------------+
| Get a list of all credentials for a single user  |  GET   |  /api/v1/user_credentials/           |
+--------------------------------------------------+--------+--------------------------------------+
| Get a list of all credentials for  a course      |  GET   |  /api/v1/course_credentials/         |
+--------------------------------------------------+--------+--------------------------------------+
| Get a list of all credentials for a program      |  GET   |  /api/v1/program_credentials/        |
+--------------------------------------------------+--------+--------------------------------------+


Get a Specific Credential for a Single User
-------------------------------------------

To get information about a specific credential for a single user, use ``credential_id``.

**Example Request**

.. code-block:: bash

    /api/v1/user_credentials/1

**Example Response**

.. code-block:: json

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


Get a List of Credentials
-------------------------

List endpoints are used to get a list of user, course, and program credentials.
All list endpoints show 20 records per page.


Get a List of All Credentials for a User
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

To get a list of all credentials that a user has earned, use ``user_credentials``.
You must include the ``username`` parameter in the query string.

This endpoint does not allow you to get a list of all credentials for all users.
You can filter the returned list of credentials by using the ``username``
or ``status`` parameters in the query string.

**Example Requests**

.. code-block:: bash

    api/v1/user_credentials/?username=<username>
    api/v1/user_credentials/?username=<username>&status=<status>

**Example Response**

.. code-block:: json

    {
        "count": 1,
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
            },
        ]
    }

**Note:**
If you do not include the ``username`` parameter, you receive the following
``status_code=400`` error message:

``A username query string parameter is required for filtering user credentials.``


Get a List of All Credentials for a Course
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

To get a list of all credentials that users have earned for a specific course,
use ``course_credentials``. You must include the ``course_id`` parameter in the
query string.

This endpoint does not allow you to get a list of all credentials for all users
in all courses.

You can filter the returned list of credentials by using
the ``course_id``, ``certificate_type``, or ``status`` parameters in the query
string.

**Example Requests**

.. code-block:: bash

    api/v1/course_credentials/?course_id=<course_id>
    api/v1/course_credentials/?course_id=<course_id>&status=<status>
    api/v1/course_credentials/?course_id=<course_id>&certificate_type=<certificate_type>
    api/v1/course_credentials/?course_id=<course_id>&status=<status>&certificate_type=<certificate_type>

**Example Response**

.. code-block:: json

    {
        "count": 1,
        "next": null,
        "previous": null,
        "results": [
            {
                "id": 3,
                "username": "admin",
                "credential": {
                    "credential_id": 1,
                    "course_id": "course-v1:ASUx+AST111+3T2015",
                    "certificate_type": "honor"
                },
                "status": "awarded",
                "download_url": "www.example.com",
                "uuid": "bbed53ff-9d5f-4bf0-9289-2fe94fda4363",
                "attributes": [
                    {
                        "name": "whitelist_reason",
                        "value": "Your reason for whitelisting."
                    }
                ],
                "created": "2015-12-21T10:22:24.367026Z",
                "modified": "2015-12-22T11:18:11.851280Z",
                "certificate_url": "http://0.0.0.0:8004/credentials/bbed53ff9d5f4bf092892fe94fda4363/"
            }
        ]
    }

**Note:**
If you do not include the ``course_id`` parameter, you receive the following
``status_code=400`` error message:

``A course_id query string parameter is required for filtering user credentials.``


Get a List of All Credentials for a Program
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

To get a list of all credentials that users have earned for a specific program,
use ``program_credentials``. The query string must include the ``program_id``
parameter.

This endpoint does not allow you to get a list of all credentials for all users
in all programs.

You can filter the returned list of credentials by using
the ``program_id`` or ``status`` parameters in the query string.

**Example Requests**

.. code-block:: bash

    api/v1/program_credentials/?program_id=<program_id>
    api/v1/program_credentials/?program_id=<program_id>&status=<status>

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

**Note:**
If you do not include the ``program_id`` parameter, you receive the following
``status_code=400`` error message:

``A course_id query string parameter is required for filtering user credentials.``
