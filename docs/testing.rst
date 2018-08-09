Testing
=======

All the below commands should be run from inside the credentials container.

The command below runs all of the Python and JS tests:

.. code-block:: bash

    $ make tests

Code quality validation (e.g. linters) can be run independently with:

.. code-block:: bash

    $ make quality
    
The Python tests can be run independantly with:

.. code-block:: bash

    $ pytest --ds credentials.settings.test
    
The react js tests can be run independantly with:

.. code-block:: bash

    $ make test-react
    
The js quality tests can be run independantly with:

.. code-block:: bash

    $ make quality-js
    

Writing Python Tests
-------------
Tests should be written for all new features. The `Django docs`_ are a good resource for learning how to test Django code.

.. _Django docs: https://docs.djangoproject.com/en/1.8/topics/testing/


Writing JS tests
----------------
All new front-end features should be made with React, subsequently, all tests written for those features should use the Jest testing framework.

Acceptance Testing
------------------
**Note: The acceptance test framework is not currently operational**

The project also includes acceptance tests used to verify behavior which relies on external systems like the LMS,
programs. At a minimum, these tests should be run against a staging environment before deploying
code to production to verify that critical user workflows are functioning as expected. With the right configuration
in place, the tests can also be run locally. Below you'll find an explanation of how to configure the LMS and the
Programs Service so that the acceptance tests can be run successfully.

Definitions
***********

Definitions of commonly used terms:

* LMS: The edX Learning Management System. Course content is found here.

Programs Configuration
**********************

#. Use the Programs Django admin to create a new XSeries program consisting of the demo course which comes installed on devstack by default.

Credentials Configuration
*************************

#. In the Credentials Django admin, configure a certificate for the XSeries program created above.

LMS Configuration
*****************

Running the acceptance tests successfully requires that you first correctly configure the ``LMS``, ``Programs``, and ``Credentials``. We'll start with the ``LMS``.

#. Verify that the following settings in ``lms.env.json`` are correct::

    "CREDENTIALS_ROOT_URL": "http://localhost:8150/"
    "LMS_ROOT_URL": "http://127.0.0.1:8000"
    "OAUTH_ENFORCE_SECURE": false
    "OAUTH_OIDC_ISSUER": "http://127.0.0.1:8000/oauth2"

#. Navigate to the Django admin and verify that an OAuth2 client with the following attributes exists. If one doesn't already exist, create a new one. The client ID and secret must match the values of Credentials's ``SOCIAL_AUTH_EDX_OIDC_KEY`` and ``SOCIAL_AUTH_EDX_OIDC_SECRET`` settings, respectively. ::

    URL:  http://localhost:8150/
    Redirect URI: http://localhost:8150/complete/edx-oidc/
    Client ID: 'credentials-key'
    Client Secret: 'credentials-secret'
    Client Type: Confidential

#. Navigate to the Django admin and verify that an OAuth2 client with the following attributes exists. If one doesn't already exist, create a new one. The client ID and secret must match the values of Programs's ``SOCIAL_AUTH_EDX_OIDC_KEY`` and ``SOCIAL_AUTH_EDX_OIDC_SECRET`` settings, respectively. ::

    URL:  http://localhost:8004/
    Redirect URI: http://localhost:8004/complete/edx-oidc/
    Client ID: 'programs-key'
    Client Secret: 'programs-secret'
    Client Type: Confidential

#. In the Django admin, verify that the OAuth2 clients referred to above are designated as a trusted clients. If this isn't already the case, add the clients created above as a new trusted clients.

#. In the Django admin, create a new access token for the superuser which will be used for acceptance tests. Set the client to the OAuth2 client for credentials. Make note of this token; it is required to run the acceptance tests.

#. At a minimum, the acceptance tests require the existence of only one demo course on the LMS instance being used for testing. The edX Demonstration Course should be present by default on most LMS instances.

#. Enroll the user in the demo course, complete it, and generate a certificate. This may require using the course's instructor dashboard to allow self-service certificate generation.

Environment Variables
*********************

Our acceptance tests rely on configuration which can be specified using environment variables.

.. list-table::
   :widths: 20 60 10 10
   :header-rows: 1

   * - Variable
     - Description
     - Required?
     - Default Value
   * - ACCESS_TOKEN
     - OAuth2 access token used to authenticate requests
     - Yes
     - N/A
   * - ENABLE_OAUTH2_TESTS
     - Whether to run tests verifying that the LMS can be used to sign into Otto
     - No
     - True
   * - LMS_URL_ROOT
     - URL root for the LMS
     - Yes
     - N/A
   * - LMS_USERNAME
     - Username belonging to an LMS user to use during testing
     - Yes
     - N/A
   * - LMS_EMAIL
     - Email address used to sign into the LMS
     - Yes
     - N/A
   * - LMS_PASSWORD
     - Password used to sign into the LMS
     - Yes
     - N/A
   * - CREDENTIALS_ROOT_URL
     - URL root for credentials service
     - Yes
     - N/A

Running Acceptance Tests
************************

Run all acceptance tests by executing ``make accept``. To run a specific test, execute::

    $ nosetests -v <path/to/the/test/module>

As discussed above, the acceptance tests rely on configuration which can be specified using environment variables. For example, when running the acceptance tests against local instances of Programs and the LMS, you might run::

    $  CREDENTIALS_ROOT_URL="http://localhost:8150/" LMS_ROOT_URL="http://127.0.0.1:8000" LMS_USERNAME="<username>" LMS_EMAIL="<email address>" LMS_PASSWORD="<password>" ACCESS_TOKEN="<access token>" PROGRAM_UUID=<program_uuid> make accept

When running against a production-like staging environment, you might run::

    $ CREDENTIALS_ROOT_URL="https://credentials.stage.edx.org" LMS_URL_ROOT="https://courses.stage.edx.org" LMS_USERNAME="<username>" LMS_EMAIL="<email address>" LMS_PASSWORD="<password>" ACCESS_TOKEN="<access token>" PROGRAM_UUID=<program_uuid> make accept
