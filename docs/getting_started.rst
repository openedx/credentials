Getting Started
===============

If you have not already done so, create/activate a `virtualenv`_. Unless otherwise stated, assume all terminal code
below is executed within the virtualenv.

.. _virtualenv: https://virtualenvwrapper.readthedocs.org/en/latest/


Install dependencies
--------------------
Dependencies can be installed via the command below.

.. code-block:: bash

    $ make requirements


Local/Private Settings
----------------------
When developing locally, it may be useful to have settings overrides that you do not wish to commit to the repository.
If you need such overrides, create a file :file:`credentials/settings/private.py`. This file's values are
read by :file:`credentials/settings/local.py`, but ignored by Git.


Configure the Amazon S3 Storage Backend
---------------------------------------
When you deploy the credentials on a staging or production server, you must change the settings to use the
`Amazon S3 storage backend`_ instead of Django's default file storage backend
(``django.core.files.storage.FileSystemStorage``) so that you do not commit changes to the repository.

To change the settings, SSH into the system, and then update the :file:`/edx/etc/credentials.yml` file.
This file's values are read by :file:`credentials/settings/production.py`, but ignored by Git.

.. highlight:: yaml

The following example shows how to use the Amazon S3 storage backend::

    AWS_STORAGE_BUCKET_NAME: credentials-s3-bucket-name
    AWS_ACCESS_KEY_ID: AAAAAAAAAAAAAAA
    AWS_SECRET_ACCESS_KEY: BBBBBBBBBBBBBBBBBBBB
    AWS_DEFAULT_ACL: ''

.. _Amazon S3 storage backend: http://django-storages.readthedocs.org/en/latest/backends/amazon-S3.html


Configure edX OAuth
-------------------
This service relies on the LMS serves as the OAuth 2.0 authentication provider.

Configuring credentials to work with OAuth requires registering a new client with the authentication
provider and updating the Django settings for this project with the client credentials.

A new OAuth 2.0 client can be created at ``http://localhost:18000/admin/oauth2_provider/application/``.

    1. Click the :guilabel:`Add Application` button.
    2. Leave the user field blank.
    3. Specify the name of this service, ``credentials``, as the client name.
    4. Set the :guilabel:`URL` to the root path of this service: ``http://localhost:8150/``.
    5. Set the :guilabel:`Redirect URL` to the complete endpoint: ``http://localhost:18150/complete/edx-oauth2/``.
    6. Copy the :guilabel:`Client ID` and :guilabel:`Client Secret` values. They will be used later.
    7. Select :guilabel:`Confidential` as the client type.
    8. Select :guilabel:`Authorization code` as the authorization grant type.
    9. Click :guilabel:`Save`.

Now that you have the client credentials, you can update your settings (ideally in
:file:`credentials/settings/local.py`). The table below describes the relevant settings.

+-----------------------------------+----------------------------------+--------------------------------------------------------------------------+
| Setting                           | Description                      | Value                                                                    |
+===================================+==================================+==========================================================================+
| SOCIAL_AUTH_EDX_OAUTH2_KEY        | OAuth 2.0 client key             | (This should be set to the value generated when the client was created.) |
+-----------------------------------+----------------------------------+--------------------------------------------------------------------------+
| SOCIAL_AUTH_EDX_OAUTH2_SECRET     | OAuth 2.0 client secret          | (This should be set to the value generated when the client was created.) |
+-----------------------------------+----------------------------------+--------------------------------------------------------------------------+
| SOCIAL_AUTH_EDX_OAUTH2_URL_ROOT   | OAuth 2.0 authentication URL     | http://127.0.0.1:18000/oauth2                                            |
+-----------------------------------+----------------------------------+--------------------------------------------------------------------------+

Service User
==============
The Open edX Credentials service must communicate with other Open edX services, such as the LMS or Platform services.
Because certificates are publicly accessible, edX provides a “Credentials service user” account that uses JWT authentication to communicate between the Credentials service and other Open edX services.
The Credentials service user makes requests on behalf of the Credentials service to access required APIs and fetch data. The Credentials service user is only available for internal use in Open edX services.

By default, the username for the Credentials service user is ``credentials_service_user``. You can change the username of the Credentials service user in the ``CREDENTIALS_SERVICE_USER`` configuration setting.
However, the Credentials service assumes that a service user named ``credentials_service_user`` is present in all needed services.

The Credentials service user must have the following characteristics.

* The service user must have the Admin role.
* The service user must have a password that is very difficult to guess so that the account cannot be accessed from web interfaces.
* The service user must be available in all of the services that the Credentials service must communicate with if these services do not require real user names.

Run migrations
--------------
Local installations use SQLite by default. If you choose to use another database backend, make sure you have updated
your settings and created the database (if necessary). Migrations can be run with `Django's migrate command`_.

.. code-block:: bash

    $ python manage.py migrate

.. _Django's migrate command: https://docs.djangoproject.com/en/1.11/ref/django-admin/#django-admin-migrate


Run the server
--------------
The server can be run with `Django's runserver command`_. If you opt to run on a different port, make sure you update
OAuth2 client via LMS admin.

.. code-block:: bash

    $ python manage.py runserver 8150

.. _Django's runserver command: https://docs.djangoproject.com/en/1.11/ref/django-admin/#django-admin-runserver
