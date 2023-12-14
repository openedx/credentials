Credentials API
===============

+-------------------------------------------------------------+--------+------------------------------------------+
| Task                                                        | Method | Endpoint                                 |
+=============================================================+========+==========================================+
| Get a list of credentials                                   | GET    | /api/v2/credentials/                     |
+-------------------------------------------------------------+--------+------------------------------------------+
| Get a specific credential                                   | GET    | /api/v2/credentials/:uuid                |
+-------------------------------------------------------------+--------+------------------------------------------+
| Create a new credential                                     | POST   | /api/v2/credentials/                     |
+-------------------------------------------------------------+--------+------------------------------------------+
| Update a credential                                         | PATCH  | /api/v2/credentials/:uuid                |
+-------------------------------------------------------------+--------+------------------------------------------+
| Query for a user's earned certificates for specific courses | POST   | /api/credentials/v1/learner_cert_status/ |
+-------------------------------------------------------------+--------+------------------------------------------+


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

Query for an individual learner's earned certificates for specific courses
--------------------------------------------------------------------------

Query for an individual learner's earned certificates for a list of courses or course runs.

**Note**:

* You must include `exactly one` of ``lms_user_id`` or ``username``.
* You must include at least one of ``courses`` and ``course_runs``, and you may include a mix of both.
    * The ``courses`` list should contain a list of course UUIDs.
    * The ``course_runs`` list should contain a list of course run keys.

If the ``username`` or ``lms_user_id`` has not earned any certificates, this endpoint
will return successfully, and the ``status`` object will be empty.

**Example Request**

.. code-block:: text

    POST api/credentials/v1/learner_cert_status/

.. code-block:: json

    {
        "username": "sample_user",
        "courses": [
            "4ad04e84-1512-11ee-be56-0242ac120002",
            "4ad051fe-1512-11ee-be56-0242ac120002"
        ],
        "course_runs": [
            "course-v1:edX+AA302+2T2023a"
        ]
    }

**Example Response**

In this example, this user has earned a certificate in only one of the courses requested, so that is the only returned value.

.. code-block:: json

    {
        "lms_user_id": 3,
        "username": "sample_user",
        "status": [
            {
            "course_uuid": "4ad04e84-1512-11ee-be56-0242ac120002",
            "course_run": {
                "uuid": "4747fefb-6f31-4689-bcfb-8ff32da191f4",
                "key": "course-v1:edX+AA302+2T2023a"
                },
            "status": "awarded",
            "type": "verified",
            "certificate_available_date": null,
            "grade": {
                "letter_grade": "Pass",
                "percent_grade": 1,
                "verified": true
                }
            }
        ]
    }

Query for multiple learners' earned certificates for specific courses
--------------------------------------------------------------------------

Query for multiple learners' earned certificates for a list of courses or course runs.

**Note**:

For each requested response:

* You must include `exactly one` of ``lms_user_id`` or ``username``.
* You must include at least one of ``courses`` and ``course_runs``, and you may include a mix of both.
    * The ``courses`` list should contain a list of course UUIDs.
    * The ``course_runs`` list should contain a list of course run keys.

If the ``username`` or ``lms_user_id`` has not earned any certificates, the ``status`` object will be empty.

**Example Request**

.. code-block:: text

    POST api/credentials/v1/bulk_learner_cert_status/

.. code-block:: json

    [
        {
            "username": "sample_user",
            "courses": [
                "4ad04e84-1512-11ee-be56-0242ac120002",
                "4ad051fe-1512-11ee-be56-0242ac120002"
            ],
            "course_runs": [
                "course-v1:edX+AA302+2T2023a"
            ]
        },
        {
            "lms_user_id":  8674309,
            "courses": [
                "4ad04e84-1513-11ee-be56-0242ac12000f",
                "4ad051fe-1513-11ee-be56-0242ac12000f"
            ],
            "course_runs": [
                "course-v1:edX+ZZ302+2T2023a"
            ]
        }
    ]

**Example Response**

In this example, the first user has earned a certificate in only one of the courses requested,  and the second user hasn't earned a certificate at
all, so there is only one return value.

.. code-block:: json

    [
        {
            "lms_user_id": 3,
            "username": "sample_user",
            "status": [
                {
                "course_uuid": "4ad04e84-1512-11ee-be56-0242ac120002",
                "course_run": {
                    "uuid": "4747fefb-6f31-4689-bcfb-8ff32da191f4",
                    "key": "course-v1:edX+AA302+2T2023a"
                    },
                "status": "awarded",
                "type": "verified",
                "certificate_available_date": null,
                "grade": {
                    "letter_grade": "Pass",
                    "percent_grade": 1,
                    "verified": true
                    }
                }
            ]
        }
    ]
