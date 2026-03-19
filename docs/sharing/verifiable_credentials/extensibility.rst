.. _vc-extensibility:

Extensibility
=============

Both :ref:`data models <vc-data-models>` and :ref:`storages <vc-storages>` may be implemented as installable pluggable applications for the Credentials IDA.

.. _vc-storages:

Storages
--------

Storage backend classes describe a destination for issued verifiable credentials.
Storages represent wallet integrations (mobile or web applications).

See available options on the :ref:`Storages page <vc-storages-page>`.

.. note::

    For a storage plugin example, see the `openedx-wallet`_ dummy internal storage (by `Raccoon Gang`_).

.. _vc-data-models:

Data Models
-----------

Data model classes are `DRF`_ serializers that compose verifiable credentials
according to different specifications.

Credentials data models
~~~~~~~~~~~~~~~~~~~~~~~

There are 3 specifications included by default:

- `Open Badges Specification v3.0`_ (see `OB3.0 model`_)
- `Open Badges Specification v3.0.1`_ (see `OB3.0.1 model`_)
- `Verifiable Credentials Data Model v1.1`_ (see `VC1.1 model`_) - experimental

Additional specifications may be implemented as separate plugins.

Credentials status information
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

:ref:`Status List v2021 <vc-status-list-api>` is a special kind of verifiable
credential. It serves as a verification mechanism for issued verifiable
credentials (meaning, it does not carry achievement information itself but
acts as a registry of statuses for all created achievement-related verifiable
credentials). Status information allows instant checks to determine whether
a presented verifiable credential is still valid. The credential issuer can
invalidate a verifiable credential by updating its indexed record in the
status list.

See full specification in the `Verifiable Credential Status List v2021`_ community report.



.. _Verifiable Credentials Data Model v1.1: https://www.w3.org/TR/vc-data-model-1.1/
.. _Open Badges Specification v3.0: https://1edtech.github.io/openbadges-specification/ob_v3p0.html
.. _Open Badges Specification v3.0.1: https://www.imsglobal.org/spec/ob/v3p0/impl/
.. _Verifiable Credential Status List v2021: https://www.w3.org/community/reports/credentials/CG-FINAL-vc-status-list-2021-20230102/
.. _Raccoon Gang: https://raccoongang.com
.. _Learner Credential Wallet: https://lcw.app
.. _DRF: https://www.django-rest-framework.org/
.. _VC1.1 model: https://github.com/openedx/credentials/blob/master/credentials/apps/verifiable_credentials/composition/verifiable_credentials.py
.. _OB3.0 model: https://github.com/openedx/credentials/blob/master/credentials/apps/verifiable_credentials/composition/open_badges.py
.. _OB3.0.1 model: https://github.com/openedx/credentials/blob/master/credentials/apps/verifiable_credentials/composition/open_badges.py
.. _openedx-wallet: https://github.com/raccoongang/openedx-wallet
