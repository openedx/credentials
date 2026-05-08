Verifiable Credentials
======================

Traditional certificates (PDFs, images) are easy to forge and hard to verify.
Employers and institutions that receive them must contact the issuing organization
to confirm authenticity - a slow, manual process that doesn't scale.

`Verifiable Credentials`_ (VCs) solve this problem. A VC is a digitally signed,
tamper-proof data object that any party can verify instantly, without contacting
the issuer. The `W3C Verifiable Credentials Data Model`_ and related
specifications define the standard.

If you want to install and configure this feature, start with the :ref:`Quick Start <vc-quickstart>` guide.
If you want to understand the main concepts and architecture first, continue with this overview and the linked reference pages.

Credentials ecosystem
---------------------

Three roles participate in the learner credentials ecosystem. For a broader standards-based description, see the `W3C VC ecosystem overview <https://www.w3.org/TR/vc-overview/#ecosystem-overview>`_.

- **Learner** - holds portable, privacy-preserving proof of achievements
  in a digital wallet and shares them with employers, institutions, or
  professional networks. For supported wallets, see :ref:`vc-storages-page`.
- **Issuer** - creates and signs credentials. The cryptographic signature
  ties each credential back to the issuing organization, making
  authenticity independently verifiable. For issuer setup, see :ref:`vc-configuration`.
- **Verifier** - validates a credential's signature and revocation status
  without contacting the issuer directly, using a public
  :ref:`Status List <vc-status-list-api>`.


Verifiable credentials lifecycle
--------------------------------

The W3C VC specification defines a standard lifecycle with three participants:

- **Issuer** (``did:web:domain.university.org``) - creates and signs
  verifiable credentials, can revoke them.
- **Holder** (``did:key:[unique-id]``) - receives, stores, and transfers
  VCs. Presents a VC or a Verifiable Presentation (VP) to verifiers.
- **Verifier** - checks the credential's signature and consults a
  Verifiable Data Registry (e.g. the issuer's Status List) to confirm the
  credential has not been revoked or expired.

.. figure:: ../../_static/images/sharing/vc_lifecycle.png
   :alt: Verifiable credentials lifecycle showing an issuer creating and revoking credentials, holders storing and presenting them, and verifiers checking status through the issuer's public registry.

This lifecycle highlights the three core phases: issuance to the holder, presentation to a verifier, and independent status checking after issuance.

Decentralized identifiers (DIDs)
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

Both issuers and holders are identified by
`Decentralized Identifiers (DIDs) <https://www.w3.org/TR/did-core/>`_.
A DID follows the format ``did:[method]:[unique-uri]``. Common methods include:

- ``did:key`` - self-contained, no external resolution needed. Used for learner (holder) identifiers.
- ``did:web`` - resolved via the issuer's domain over HTTPS. Used for institutional issuers.
- ``did:ethr`` - resolved via Ethereum blockchain.

A DID resolves to a **DID Document** containing the public key material needed to verify signatures. For implementation details on how Open edX uses DIDs, see :ref:`vc-tech-details`.

How It Works in Open edX
------------------------

The Verifiable Credentials feature is optional. Once enabled, it extends the
Credentials service and Learner Record micro-frontend.

Open edX Credentials provides the issuance mechanism: it prepares the credential,
signs it with the configured issuer key, and exposes the APIs needed by the
wallet flow. The issuer itself is the organization or entity represented by the
configured issuer DID and issuer name.

A single Open edX achievement can be used as a source for multiple verifiable
credentials, each using a different data model if needed. The typical flow
looks like this.

#. A learner earns an Open edX credential (course or program certificate).
#. The learner visits the Learner Record page and requests a verifiable
   credential. The platform generates a deep link or QR code.
#. The learner scans the QR code or follows the deep link to open their
   digital wallet app.
#. The digital wallet sends an issuance request back to the platform. The
   platform signs the credential using the configured issuer's private key
   and returns it to the wallet.
#. The learner can now present the VC to any relying party.
#. The relying party verifies the signature and checks the issuer's public
   status list to confirm the credential is still valid (not expired or
   revoked).

See :ref:`vc-components` for the main system components, :ref:`vc-status-list-api` for status verification, and :ref:`vc-storages-page` for wallet behavior and learner flow.

The feature supports multiple verifiable credential specifications. For supported data formats and their extensibility model, see :ref:`vc-extensibility`. The built-in production wallet integration is LCWallet. For storage details, including the development wallet, see :ref:`vc-storages-page`.

.. seealso::

   :ref:`vc-quickstart`
      Installation and first-time setup for verifiable credentials.

   `W3C Verifiable Credentials Overview <https://www.w3.org/TR/vc-overview/>`_
      Standards background for the VC ecosystem, lifecycle, and trust model.

   `W3C Decentralized Identifiers (DID) v1.0 <https://www.w3.org/TR/did-core/>`_
      Core specification for decentralized identifiers and DID documents.

----

.. toctree::
    :maxdepth: 1

    quickstart
    components
    configuration
    managing
    extensibility
    composition
    storages
    tech_details
    api_reference

.. _Verifiable Credentials: https://en.wikipedia.org/wiki/Verifiable_credentials
.. _W3C Verifiable Credentials Data Model: https://www.w3.org/TR/vc-data-model-1.1/
