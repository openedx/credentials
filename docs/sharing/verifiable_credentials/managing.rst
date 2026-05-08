.. _vc-managing:

Managing Verifiable Credentials
===============================

Monitoring issuance lines
-------------------------

Track issuance activity at ``<credentials-host>/admin/verifiable_credentials/issuanceline/``. Each record shows the processing status, storage backend, and linked Open edX credential.

Filter by processing status to identify failed issuances that may need investigation.

Managing issuers
----------------

Multiple ``IssuanceConfiguration`` records can exist at ``<credentials-host>/admin/verifiable_credentials/issuanceconfiguration/``, but only the last enabled record is the active issuer.

- To rotate issuer credentials, create a new configuration with updated keys and enable it.
- The admin interface prevents disabling the last enabled configuration. Use the ``remove_issuance_configuration`` management command to delete one entirely. See :ref:`vc-management-commands`.

Revoking credentials
--------------------

When an Open edX credential (course or program certificate) is revoked, all verifiable credentials issued from that achievement are automatically revoked via a Django ``post_save`` signal. The revocation is reflected in the issuer's :ref:`Status List <vc-status-list-api>`, allowing relying parties to detect revoked credentials during verification.

There is no manual revocation interface. Revocation flows from the underlying Open edX credential status.

.. seealso::

   :ref:`vc-configuration`
      Feature flags, issuer settings, and management commands.

   :ref:`vc-quickstart`
      Step-by-step initial setup guide.

   :ref:`vc-tech-details`
      Internal implementation details for debugging and customization.
