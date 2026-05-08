.. _vc-quickstart:

Quick Start
===========

Set up Verifiable Credentials issuing for your Open edX instance. By the end of this guide you will have a working issuance configuration that lets learners receive and store verifiable credentials.

.. contents:: Steps
    :local:
    :class: no-bullets

1. Prerequisites and installation
---------------------------------

The Credentials service must be installed and running on your Open edX instance.

Option A: Using Tutor (recommended)
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

#. Install the `tutor-credentials`_ plugin (provides the Credentials service):

   .. code-block:: bash

       pip install tutor-credentials

#. Install the `tutor-contrib-badges`_ plugin (enables verifiable credentials feature flags, configures the event bus, and sets up certificate synchronization):

   .. code-block:: bash

       pip install git+https://github.com/raccoongang/tutor-contrib-badges@main

   See the `tutor-contrib-badges README <https://github.com/raccoongang/tutor-contrib-badges#readme>`_ for additional details.

#. Enable the necessary plugins:

   .. code-block:: bash

       tutor plugins enable discovery mfe credentials badges

#. Rebuild images and launch:

   .. code-block:: bash

       tutor images build openedx discovery credentials
       tutor local launch

The plugin automatically enables ``ENABLE_VERIFIABLE_CREDENTIALS`` for both the Credentials service and Learner Record MFE, and configures event bus consumers for certificate lifecycle events.

.. _tutor-credentials: https://github.com/overhangio/tutor-credentials
.. _tutor-contrib-badges: https://github.com/raccoongang/tutor-contrib-badges

Option B: Other installations
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

#. Install the Credentials service following the `Getting Started <https://edx-credentials.readthedocs.io/en/latest/getting_started.html>`_ guide.

#. Enable verifiable credentials in the Credentials service settings:

   .. code-block:: python

       ENABLE_VERIFIABLE_CREDENTIALS = True

#. Enable verifiable credentials in the Learner Record MFE ``.env`` file:

   .. code-block:: text

       ENABLE_VERIFIABLE_CREDENTIALS=true

For all available settings, see :ref:`vc-configuration`.

2. Generate issuer credentials
------------------------------

Each issuer_ must have its own decentralized identifier (DID) and private key.
Unless you already have them, generate a new pair by using the management command provided by the Credentials service.

If you are using Tutor:

.. code-block:: bash

    tutor local exec credentials ./manage.py generate_issuer_credentials

For other installations, run the command directly in the Credentials service:

.. code-block:: bash

    ./manage.py generate_issuer_credentials

Example output:

.. code-block:: text

    {
        'did': 'did:key:z6MkgdiV7pVPCapM8oUwfhxBwYZgh8dXkHkJykSAc4DHKD7X',
        'private_key': '{"kty":"OKP","crv":"Ed25519","x":"IGUT8E_aRNzLqouWO4zdeZ6l4CEXsVmJDOpOQS69m7o","d":"vn8xgdO5Ki3zlvRNc2nUqcj50Ise1Vl1tlbs9DUL"}'
    }

.. list-table:: Output fields
   :widths: 20 80
   :header-rows: 1

   * - Field
     - Description
   * - ``did``
     - Unique issuer decentralized identifier (DID). Used as the **Issuer id** in the admin configuration.
   * - ``private_key``
     - Issuer private key in JWK format (stringified JSON). Used as the **Issuer key** in the admin configuration.

.. warning::

   Treat the ``private_key`` value as a secret. Store it securely, do not commit it to version control, and do not expose it in logs, screenshots, or shared configuration examples.

For additional management commands, see :ref:`vc-management-commands`.

3. Configure issuer credentials
-------------------------------

Use the generated credentials to replace the stub values in the auto-created
Issuance Configuration.

#. In the Credentials admin panel, navigate to ``https://<your-credentials-host>/admin/verifiable_credentials/issuanceconfiguration/``.
#. Open the auto-created Issuance Configuration entry.

   .. figure:: ../../_static/images/verifiable_credentials-issuer-configuration.png
      :alt: Issuer configuration form in Django admin showing the Issuer id, Issuer key, and Issuer name fields.

   a. Set the **Issuer id** to the generated ``did`` value.
   b. Set the **Issuer key** to the generated ``private_key`` value.
   c. Set the **Issuer name** to a verbose name for your issuer.

   .. note::

      The **Issuer key** must be a stringified JSON value, that is, an escaped JSON string rather than a raw JSON object. The ``generate_issuer_credentials`` command outputs it in the correct format.

#. Make sure the configuration is enabled and click **Save**.

For full admin panel reference, see :ref:`vc-administration-site`.

4. Verify status list accessibility
-----------------------------------

The Status List API endpoint is crucial for the feature. Once everything is
configured correctly, it must be publicly available:

.. code::

    # each issuer maintains its own Status List; <issuer-did> is the ``did`` value from step 1:
    https://<your-credentials-host>/verifiable_credentials/api/v1/status-list/2021/v1/<issuer-did>/

For endpoint details and response format, see :ref:`vc-status-list-api`.

5. Register the issuer for Learner Credential Wallet
----------------------------------------------------

The built-in storage backend is the `Learner Credential Wallet <https://lcw.app/>`_ (LCWallet), which is a mobile app by the Digital Credentials Consortium. LCWallet only accepts credentials from allow-listed issuers.

To register your issuer, open a pull request in the `community issuer registry`_ adding your issuer's DID (the ``did`` value from step 1) to ``registry.json``, matching the format of existing entries. Once the registry maintainers merge your PR, LCWallet will accept credentials from your instance.

For development and testing, use the `Sandbox Registry`_ and submit a PR there with the same format.

For more information about LCWallet, including learner flow and usage details, see :ref:`vc-storages-page`.

.. seealso::

   :ref:`vc-configuration`
      Feature flags, issuer settings, and management commands.

   :ref:`vc-management-commands`
      Additional commands for issuer and status list management.

   :ref:`vc-administration-site`
      Django admin pages for issuer configuration and issuance lines.

   :ref:`vc-status-list-api`
      Status List API endpoint details and response examples.

   :ref:`vc-storages-page`
      Learner Credential Wallet details, learner flow, and storage behavior.

   :ref:`vc-components`
      Components, admin pages, and Status List API details.

.. _community issuer registry: https://github.com/digitalcredentials/community-registry
.. _Sandbox Registry: https://github.com/digitalcredentials/sandbox-registry

.. _issuer: https://www.w3.org/TR/vc-data-model-1.1/#dfn-issuers
