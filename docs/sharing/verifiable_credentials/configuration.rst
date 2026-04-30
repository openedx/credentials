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

Learner Record MFE settings
---------------------------

The `Learner Record MFE <https://github.com/openedx/frontend-app-learner-record>`_ uses environment variables configured in its ``.env`` file:

``ENABLE_VERIFIABLE_CREDENTIALS`` - enables the verifiable credentials UI routes.

``SUPPORT_URL_VERIFIABLE_CREDENTIALS`` - footer support link on verifiable credentials pages.

Credentials service settings
-----------------------------

``ENABLE_VERIFIABLE_CREDENTIALS`` (boolean) - main feature flag for the backend.

The feature introduces its own set of default settings, namespaced under the
``VERIFIABLE_CREDENTIALS`` setting:

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

Default settings
----------------

All settings are defined under the ``VERIFIABLE_CREDENTIALS`` dictionary
(see ``verifiable_credentials/settings.py`` for source).

.. list-table::
   :header-rows: 1
   :widths: 30 70

   * - Setting
     - Description / Default
   * - ``DEFAULT_DATA_MODELS``
     - Dotted paths to :ref:`data model <vc-data-models>` classes. At least one must be available, and every configured storage must reference an available data model.

       **Default:** ``["credentials.apps.verifiable_credentials.composition.verifiable_credentials.VerifiableCredentialsDataModel", "credentials.apps.verifiable_credentials.composition.open_badges.OpenBadgesDataModel"]``
   * - ``DEFAULT_STORAGES``
     - Dotted paths to :ref:`storage <vc-storages>` classes. At least one must be available.

       **Default:** ``["credentials.apps.verifiable_credentials.storages.learner_credential_wallet.LCWallet"]``
   * - ``STATUS_LIST_LENGTH``
     - Per-issuer credential cap. Each issuer has a monotonically increasing status index capped by this value (``unique_together`` constraint). Increase it or create additional issuers to issue more credentials. For details see the `Status List 2021 specification <https://www.w3.org/community/reports/credentials/CG-FINAL-vc-status-list-2021-20230102/#revocation-bitstring-length>`_.

       **Default:** ``10000`` (16 KB)
   * - ``STATUS_LIST_STORAGE``
     - Storage class for the status list implementation.

       **Default:** ``"credentials.apps.verifiable_credentials.storages.status_list.StatusList2021"``
   * - ``STATUS_LIST_DATA_MODEL``
     - Data model class for the status list implementation.

       **Default:** ``"credentials.apps.verifiable_credentials.composition.status_list.StatusListDataModel"``
   * - ``DEFAULT_ISSUANCE_REQUEST_SERIALIZER``
     - Serializer for incoming issuance requests.

       **Default:** ``"credentials.apps.verifiable_credentials.issuance.serializers.IssuanceLineSerializer"``
   * - ``DEFAULT_RENDERER``
     - Renderer for outgoing verifiable credential responses.

       **Default:** ``"credentials.apps.verifiable_credentials.issuance.renderers.JSONLDRenderer"``

DEFAULT_ISSUER
~~~~~~~~~~~~~~

Issuer identity used during the first deployment data migration.
Multiple ``IssuanceConfiguration`` records can exist in the database, but
only the last enabled record is the active issuer for all verifiable
credentials.

.. important::
   The admin interface prevents disabling the last enabled configuration.
   Use ``remove_issuance_configuration`` to delete one entirely.

.. list-table::
   :header-rows: 1
   :widths: 20 80

   * - Key
     - Description / Default
   * - ``NAME``
     - Verbose issuer name embedded in each verifiable credential.

       **Default:** ``"Default (system-wide)"``
   * - ``KEY``
     - Private JWK used for signing. Use your own key or generate one with the ``generate_issuer_credentials`` command below.

       **Default:** placeholder (must be replaced)
   * - ``ID``
     - Decentralized Identifier (DID) derived from the private key.

       **Default:** placeholder (must be replaced)

.. _vc-management-commands:

Management commands
-------------------

All commands below run in the **Credentials service**.

.. _vc-issuer-credentials-helper:

``generate_issuer_credentials``
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

Generates a new private key (JWK) and a decentralized identifier (DID) for an
issuer.

.. code-block:: sh

    ./manage.py generate_issuer_credentials
    >> {
        'did': 'did:key:z6MkgdiV7pVPCapM8oUwfhxBwYZgh8dXkHkJykSAc4DHKD7X',
        'private_key': '{"kty":"OKP","crv":"Ed25519","x":"IGUT8E_aRNzLqouWO4zdeZ6l4CEXsVmJDOpOQS69m7o","d":"vn8xgdO5Ki3zlvRNc2nUqcj50Ise1Vl1tlbs9DUL-hg"}'
       }

``create_default_issuer``
~~~~~~~~~~~~~~~~~~~~~~~~~

Creates an Issuance Configuration from ``VERIFIABLE_CREDENTIALS[DEFAULT_ISSUER]``
settings. A default configuration is created automatically during the first
deployment via data migration. Use this command to re-create it if needed.

.. code-block:: sh

    ./manage.py create_default_issuer

``remove_issuance_configuration``
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

Removes an issuer configuration by its DID. The admin interface only allows
deactivation, not deletion.

.. code-block:: sh

    ./manage.py remove_issuance_configuration did:key:<UNIQUE_DID_KEY>

.. _vc-status-list-helper:

``generate_status_list``
~~~~~~~~~~~~~~~~~~~~~~~~

Generates a signed Status List 2021 credential for a given issuer. Useful for
debugging revocation status or verifying the status list is correctly formed.

.. code-block:: sh

    ./manage.py generate_status_list did:key:<UNIQUE_DID_KEY>

