This is a directory containing old end-to-end (e2e) test code. It is bit-rotten and needs some attention (and likely movement into our end-to-end test suite - see `LEARNER-6164`_).

Note that it does not even have a ``__init__.py`` - this is not for current use. Also, these used to live one directory up and their imports have not been changed to adjust.

.. _LEARNER-6164: https://openedx.atlassian.net/browse/LEARNER-6164


Below are some old docs for this code:


Acceptance Testing
------------------

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

#. In the Credentials Django admin, configure a certificate for the XSeries program created above. Note the UUID for this, you'll use it later.

#. Download the geckodriver package, untar it, and copy the executable into the container's /usr/local/bin:

curl -L https://github.com/mozilla/geckodriver/releases/download/v0.21.0/geckodriver-v0.21.0-linux64.tar.gz | tar xzf - -C /usr/local/bin/

# apt install firefox xvfb


LMS Configuration
*****************

Running the acceptance tests successfully requires that you first correctly configure the ``LMS`` and ``Credentials``. We'll start with the ``LMS``, assuming a standard devstack installation.

#. In the Django admin, create a new access token for the superuser which will be used for acceptance tests. Set the client to the OAuth2 client for credentials and the scope to be read+write. Make note of this token; it is required to run the acceptance tests. You may already have some of these tokens. In which case, you can just make note of the value for later.

#. At a minimum, the acceptance tests require the existence of only one demo course on the LMS instance being used for testing. The edX Demonstration Course should be present by default on most LMS instances.

#. Enroll the user in the demo course, complete it, and generate a certificate. This may require using the course's instructor dashboard to allow self-service certificate generation.

#. Make sure you're logged in as the user before running the tests.

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

    $ xvfb-run nosetests -v <path/to/the/test/module>

As discussed above, the acceptance tests rely on configuration which can be specified using environment variables. For example, when running the acceptance tests against local instances of Programs and the LMS, you might run::

    $ SELENIUM_BROWSER=firefox DJANGO_SETTINGS_MODULE=credentials.settings.local OAUTH2_USER_INFO_URL="http://edx.devstack.lms:18000/" CREDENTIALS_ROOT_URL="http://edx.devstack.credentials:18150/" LMS_ROOT_URL="http://edx.devstack.lms:18000" LMS_USERNAME="<username>" LMS_EMAIL="<email address>" LMS_PASSWORD="<password>" ACCESS_TOKEN="<access token>" PROGRAM_UUID=<program_uuid> xvfb-run make accept

When running against a production-like staging environment, you might run::

    $ CREDENTIALS_ROOT_URL="https://credentials.stage.edx.org" LMS_URL_ROOT="https://courses.stage.edx.org" LMS_USERNAME="<username>" LMS_EMAIL="<email address>" LMS_PASSWORD="<password>" ACCESS_TOKEN="<access token>" PROGRAM_UUID=<program_uuid> xvfb-run make accept

