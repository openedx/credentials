Configuration
=============

Verifiable Credentials feature is optional. It is disabled by default.

Learner Record micro-frontend
-----------------------------

The most of configuration is related to the Credentials IDA (`verifiable_credentials` app), but there are few UI-related settings.

``ENABLE_VERIFIABLE_CREDENTIALS`` (boolean) - enables feature appearance (extra routes)

``SUPPORT_URL_VERIFIABLE_CREDENTIALS`` (URL string) - footer support link

Verifiable Credentials application
----------------------------------

``ENABLE_VERIFIABLE_CREDENTIALS`` (boolean) - main feature flag

The feature introduces its own set of default settings which are namespaced in the VERIFIABLE_CREDENTIALS setting, like this:

.. code-block:: python

    VERIFIABLE_CREDENTIALS = {
        'DEFAULT_DATA_MODELS': [
            "credentials.apps.verifiable_credentials.composition.open_badges.OpenBadgesDataModel",
        ],
        "STATUS_LIST_LENGTH": 50000,
        "DEFAULT_ISSUER": {
            "NAME": "The University of the Digital Future",
            "KEY": '{"kty":"OKP","crv":"Ed25519","x":"IGUT8E_aRNzLqouWO4zdeZ6l4CEXsVmJDOpOQS69m7o","d":"vn8xgdO5Ki3zlvRNc2nUqcj50Ise1Vl1tlbs9DUL-hg"}',
            "ID": "did:key:z6MkgdiV7pVPCapM8oUwfhxBwYZgh8dXkHkJykSAc4DHKD7X",
        },
    }

Such configuration overrides the corresponding built-in settings:

1. Data models list narrowed down to a single specification
2. Status list length extended to 50K positions
3. Default issuer configured with concrete credentials

Built-in values
---------------

There is a set of built-in predefined settings:

.. code-block:: python

    # verifiable_credentials/settings.py

    DEFAULTS = {
        "DEFAULT_DATA_MODELS": [
            "credentials.apps.verifiable_credentials.composition.verifiable_credentials.VerifiableCredentialsDataModel",
            "credentials.apps.verifiable_credentials.composition.open_badges.OpenBadgesDataModel",
        ],
        "DEFAULT_STORAGES": [
            "credentials.apps.verifiable_credentials.storages.learner_credential_wallet.LCWallet",
        ],
        "DEFAULT_ISSUER": {
            "ID": "generate-me-with-didkit-lib",
            "KEY": "generate-me-with-didkit-lib",
            "NAME": "Default (system-wide)",
        },
        "DEFAULT_ISSUANCE_REQUEST_SERIALIZER": "credentials.apps.verifiable_credentials.issuance.serializers.IssuanceLineSerializer",
        "DEFAULT_RENDERER": "credentials.apps.verifiable_credentials.issuance.renderers.JSONLDRenderer",
        "STATUS_LIST_STORAGE": "credentials.apps.verifiable_credentials.storages.status_list.StatusList2021",
        "STATUS_LIST_DATA_MODEL": "credentials.apps.verifiable_credentials.composition.status_list.StatusListDataModel",
        "STATUS_LIST_LENGTH": 10000,
    }

Default data models
-------------------

Deployment configuration can override `data models set`_ with the respect of the following restrictions:

- there always must be at least 1 data model available
- each storage is pre-configured to use some data model which must be available

Default storages
----------------

Deployment configuration can override `storages set`_ with the respect of the following restrictions:

- there always must be at least 1 storage available


Default issuer
--------------

.. note::
    Currently, there is only a single active issuer (system-wide) available So, all verifiable credentials are created (issued) on behalf of this Issuer.

There is the `Issuance Configuration`_ database model, which initial record is created based on these settings.

NAME
~~~~

Verbose issuer name (it is placed into each verifiable credential).

KEY
~~~

A private secret key (JWK) which is used for verifiable credentials issuance (proof/digital signature generation). It can be generated with the help of the `didkit`_ Python (Rust) library.

ID
~~

A unique issuer decentralized identifier (created from a private key, `example`_).

Status List configuration
-------------------------

Length
~~~~~~

``STATUS_LIST_LENGTH`` - default = 10000 (16KB)

Possibly, the only status list settings to configure. A status sequence positions count (how many issued verifiable credentials statuses are included). See `related specs`_ for details.

Storage
~~~~~~~

``STATUS_LIST_STORAGE``

A technical storage class (allows status list implementation override).

Data model
~~~~~~~~~~

``STATUS_LIST_DATA_MODEL``

A data model class (allows status list implementation override).

----

Other settings are available for advanced tweaks but usually are not meant to be configured:

- Default issuance request serializer (incoming issuance request parsing)
- Default renderer (outgoing verifiable credential presentation)

Management commands
-------------------

There are a couple of service commands available for the verifiable_credentials application.

Issuer credentials helper
~~~~~~~~~~~~~~~~~~~~~~~~~

**Generates private key for Issuer (JWK) and a decentralized identifier (DID) based on that key.**

.. code-block:: sh

    root@credentials:/edx/app/credentials/credentials# ./manage.py generate_issuer_credentials
    >> {'did': 'did:key:z6MkgdiV7pVPCapM8oUwfhxBwYZgh8dXkHkJykSAc4DHKD7X',
 'private_key': '{"kty":"OKP","crv":"Ed25519","x":"IGUT8E_aRNzLqouWO4zdeZ6l4CEXsVmJDOpOQS69m7o","d":"vn8xgdO5Ki3zlvRNc2nUqcj50Ise1Vl1tlbs9DUL-hg"}'}

Issuer configuration helpers
~~~~~~~~~~~~~~~~~~~~~~~~~~~~

**Create initial Issuance Configuration based on deployment issuer(s) setup.**

.. code-block:: sh

    root@credentials:/edx/app/credentials/credentials# ./manage.py create_default_issuer

Initial Issuance configuration is created based on VERIFIABLE_CREDENTIALS[DEFAULT_ISSUER] via data migration during the first deployment. Helper allows manually repeat that is needed (Additional configurations can be created from django admin interface).

**Remove Issuance Configuration based on Issuer ID.**

.. code-block:: sh

    root@credentials:/edx/app/credentials/credentials# ./manage.py remove_issuance_configuration did:key:z6MkgdiV7pVPCapM8oUwfhxBwYZgh8dXkHkJykSAc4DHKD7X

Issuance configuration delete operation is forbidden in admin interface (only deactivation is available). This tool allows to cleanup configurations list if needed.

Status List helper
~~~~~~~~~~~~~~~~~~

**Generate Status List 2021 verifiable credential**

.. code-block:: sh

    root@credentials:/edx/app/credentials/credentials# ./manage.py generate_status_list did:key:z6MkgdiV7pVPCapM8oUwfhxBwYZgh8dXkHkJykSAc4DHKD7X

Allows Status List verifiable credential generation (for a given Issuer ID).

.. _data models set: extensibility.html#data-models
.. _storages set: extensibility.html#storages
.. _didkit: https://pypi.org/project/didkit/
.. _example: https://github.com/spruceid/didkit-python/blob/main/examples/python_django/didkit_django/issue_credential.py#L12
.. _related specs : https://w3c.github.io/vc-status-list-2021/#revocation-bitstring-length
.. _Issuance Configuration: components.html#administration-site