Extensibility
=============

Storages
--------

Storage backend classes describe a destination for issued verifiable credentials. Basically, storages are wallets (mobile or web applications).

See available options on `Storages page`_.

Data Models
-----------

Data model classes are `DRF`_ serializers which compose verifiable credentials of different specifications.

Credentials data models
~~~~~~~~~~~~~~~~~~~~~~~

There are 2 specifications included by default:

- `Open Badges Specification v3.0`_ (see `OB3.0 model`_)
- `Verifiable Credentials Data Model v1.1`_ (see `VC1.1 model`_) - experimental

Additional specifications may be implemented as separate `plugins`_.

Credentials status information
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

.. note::

    Status information allows instant checks to figure out if the presented verifiable credential is still valid.  The credential issuer can invalidate a verifiable credential by updating its indexed record in the status list.

`Status List v2021`_ is a special kind of verifiable credential. It serves as a mechanism of verification for issued verifiable credentials (meaning, it does not carry achievement information itself but it is a registry of statuses for all created achievement-related verifiable credentials).

- `Verifiable Credential Status List v2021`_

There are 2 parts of the approach:

- status entry (becomes a part of each issued verifiable credential and carries the info "how to check status")
- status list (an Issuer-centric separate freely reachable statuses registry)

Plugins
-------

Both `data models`_ and `storages`_ may be implemented as Credentials IDA installable pluggable applications.

.. note::

    For storage plugin example, please, see the `openedx-wallet`_ training storage (by the `Raccoon Gang`_) .

.. _Verifiable Credentials Data Model v1.1: https://www.w3.org/TR/vc-data-model-1.1/
.. _Open Badges Specification v3.0: https://1edtech.github.io/openbadges-specification/ob_v3p0.html
.. _Verifiable Credential Status List v2021: https://w3c.github.io/vc-status-list-2021/
.. _data models: extensibility.html#data-models
.. _storages: extensibility.html#storages
.. _storages page: storages.html
.. _plugins: extensibility.html#plugins
.. _Raccoon Gang : https://raccoongang.com
.. _Learner Credential Wallet: https://lcw.app
.. _DRF: https://www.django-rest-framework.org/
.. _Status List v2021: components.html#status-list-api
.. _VC1.1 model: https://github.com/openedx/credentials/tree/master/credentials/apps/verifiable_credentials/composition/verifiable_credentials.py
.. _OB3.0 model: https://github.com/openedx/credentials/tree/master/credentials/apps/verifiable_credentials/composition/open_badges.py
.. _openedx-wallet: https://github.com/raccoongang/openedx-wallet