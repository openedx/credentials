.. _vc-configuration:

Configuration
=============

The Verifiable Credentials feature is optional. It is disabled by default.

.. _vc-activation:

Conditional activation
----------------------

The ``verifiable_credentials`` app is always in ``INSTALLED_APPS``, but its URL routes, signals, and system checks
only activate when ``ENABLE_VERIFIABLE_CREDENTIALS`` is set to ``True``. After changing this setting, restart the
Credentials service for the change to take effect.

Learner Record micro-frontend
-----------------------------

Most configuration belongs to the Credentials IDA (``verifiable_credentials`` app),
but there are a few UI-related settings.

``ENABLE_VERIFIABLE_CREDENTIALS`` (boolean) - enables feature appearance (extra routes)

``SUPPORT_URL_VERIFIABLE_CREDENTIALS`` (URL string) - footer support link.
Note: this setting belongs to the Learner Record MFE
(frontend-app-learner-record), not the Credentials IDA.

The feature introduces its own set of default settings, namespaced under the
``VERIFIABLE_CREDENTIALS`` setting:

Verifiable Credentials application
----------------------------------

``ENABLE_VERIFIABLE_CREDENTIALS`` (boolean) - main feature flag

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

This configuration overrides the corresponding built-in settings:

1. Data models list narrowed down to a single specification.
2. Status list length extended to 50K positions.
3. Default issuer configured with concrete credentials.

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

Deployment configuration can override the :ref:`data models set <vc-data-models>` with respect to the following restrictions:

- there always must be at least 1 data model available
- each storage is pre-configured to use some data model which must be available

Default storages
----------------

Deployment configuration can override the :ref:`storages set <vc-storages>` with respect to the following restrictions:

- there always must be at least 1 storage available


Default issuer
--------------

.. note::
    Currently, there is only a single active issuer (system-wide) available. All verifiable credentials are created (issued) on behalf of this Issuer.

Multiple ``IssuanceConfiguration`` records can coexist. The last enabled record is the active issuer.

.. important::
    The admin interface prevents disabling the last enabled configuration. To remove a configuration entirely,
    use the :ref:`remove_issuance_configuration <vc-management-commands>` management command.

The :ref:`Issuance Configuration <vc-administration-site>` database model's initial
record is created based on these settings.

NAME
~~~~

Verbose issuer name (it is placed into each verifiable credential).

KEY
~~~

A private secret key (JWK) used for verifiable credential issuance (proof/digital
signature generation). It can be generated using the `didkit`_ Python (Rust)
library.

ID
~~

A unique issuer decentralized identifier (created from a private key, `example`_).

Status List configuration
-------------------------

Length
~~~~~~

``STATUS_LIST_LENGTH`` - default = 10000 (16KB)

The number of positions in the status sequence (how many issued verifiable credential
statuses can be tracked). Each issuer has a monotonically increasing status index
capped by this value (enforced by a ``unique_together`` constraint on ``issuer_id``
and ``status_index``). This is effectively a per-issuer credential cap. To issue more
credentials, increase this setting or create additional issuers. See `related specs`_
for details.

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

.. _vc-management-commands:

Management commands
-------------------

The following management commands are available for the ``verifiable_credentials``
application.

.. _vc-issuer-credentials-helper:

Issuer credentials helper
~~~~~~~~~~~~~~~~~~~~~~~~~

**Generates a new private key (JWK) for an Issuer and a decentralized identifier
(DID) based on that key.**

.. code-block:: sh

    ./manage.py generate_issuer_credentials
    >> {'did': 'did:key:z6MkgdiV7pVPCapM8oUwfhxBwYZgh8dXkHkJykSAc4DHKD7X',
 'private_key': '{"kty":"OKP","crv":"Ed25519","x":"IGUT8E_aRNzLqouWO4zdeZ6l4CEXsVmJDOpOQS69m7o","d":"vn8xgdO5Ki3zlvRNc2nUqcj50Ise1Vl1tlbs9DUL-hg"}'}

Issuer configuration helpers
~~~~~~~~~~~~~~~~~~~~~~~~~~~~

**Create initial Issuance Configuration based on deployment issuer(s) setup.**

.. code-block:: sh

    root@credentials:/edx/app/credentials/credentials# ./manage.py create_default_issuer

The initial Issuance configuration is created based on
``VERIFIABLE_CREDENTIALS[DEFAULT_ISSUER]`` via data migration during the first
deployment. This helper allows repeating the process manually if needed. Additional
configurations can be created from the Django admin interface.

**Remove Issuance Configuration based on Issuer ID.**

.. code-block:: sh

    ./manage.py remove_issuance_configuration did:key:<UNIQUE_DID_KEY>

This management command removes an issuer configuration. The admin interface only
allows deactivation, not deletion.

.. _vc-status-list-helper:

Status List helper
~~~~~~~~~~~~~~~~~~

**Generate Status List 2021 verifiable credential**

.. code-block:: sh

    ./manage.py generate_status_list did:key:<UNIQUE_DID_KEY>

Generates a signed Status List 2021 credential for a given Issuer ID. Useful for debugging revocation status or
verifying the status list is correctly formed.

.. _didkit: https://pypi.org/project/didkit/
.. _example: https://github.com/spruceid/didkit-python/blob/main/examples/python_django/didkit_django/issue_credential.py#L12
.. _related specs: https://www.w3.org/community/reports/credentials/CG-FINAL-vc-status-list-2021-20230102/#revocation-bitstring-length
