.. _vc-quickstart:

Quick Start
===================================

.. contents:: Steps
    :local:
    :class: no-bullets

This guide outlines initial preparations for the Verifiable Credentials feature.

1. Feature activation
---------------------

Since Verifiable Credentials feature is optional, it must be enabled to be accessible.

.. code::

    # both Credentials service and Learner Record MFE:
    ENABLE_VERIFIABLE_CREDENTIALS = true

See :ref:`vc-configuration` for more details.

2. Issuer credentials generation
--------------------------------

Once enabled, the Verifiable Credentials feature has reasonable defaults. The only additional step needed is the issuer_ credentials setup. Unless you already have an appropriate issuer key and issuer ID, you need to generate them:

.. code::

    # use management command:
    root@credentials:/edx/app/credentials/credentials# ./manage.py generate_issuer_credentials
    >> {
        'did': 'did:key:z6MkgdiV7pVPCapM8oUwfhxBwYZgh8dXkHkJykSAc4DHKD7X',
        'private_key': '{"kty":"OKP","crv":"Ed25519","x":"IGUT8E_aRNzLqouWO4zdeZ6l4CEXsVmJDOpOQS69m7o","d":"vn8xgdO5Ki3zlvRNc2nUqcj50Ise1Vl1tlbs9DUL"}'
    }

Here:

    -  "did" - unique Issuer decentralized identifier
    -  "private_key" - Issuer private JWK

See :ref:`vc-management-commands` for more details.

3. Issuer credentials setup
---------------------------

Use the generated credentials to replace the stub values in the auto-created Issuance Configuration.

Enter Credentials Administration interface and find "VERIFIABLE CREDENTIALS" section (``/admin/verifiable_credentials/issuanceconfiguration/``).

.. code::

    Issuer id: use "did"
    Issuer key: use "private_key"
    Issuer name: will be used as issuer's verbose name

.. note::
    :class: dropdown

    Make sure the configuration is enabled.

See :ref:`vc-administration-site` for more details.

4. Ensure status list is accessible
-----------------------------------

Status List API endpoint is crucial for the feature. Once everything is configured correctly it must be publicly available:

.. code::

    # each Issuer maintains its own Status List:
    https://credentials.example.com/verifiable_credentials/api/v1/status-list/2021/v1/<issuer-did>/

See :ref:`vc-status-list-api` for more details.

5. Issuer registration (Learner Credential Wallet)
--------------------------------------------------

This step is specific for the Learner Credential Wallet storage.

See Learner Credential Wallet :ref:`usage prerequisites <vc-usage-prerequisites>`.

.. _issuer: https://www.w3.org/TR/vc-data-model-1.1/#dfn-issuers
