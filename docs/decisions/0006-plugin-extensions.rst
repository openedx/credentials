Django App Plugin extensions
============================

Status
------

Accepted


Context
-------

More functionality is planned to be added to the Credentials service as a part of
`credentials/issues/1734`_ and `credentials/issues/1736`_.
Credentials may benefit from adoption of the `Django App Plugin`_ functionality.
It would provide additional possibilities to support many integrations with third-party
services for credentials sharing, like digital credentials platforms, digital wallets,
credentials signing services, etc.

For more information on plugins in particular, see the `Django Apps Plugin README`_.

.. _`credentials/issues/1734`: https://github.com/openedx/credentials/issues/1734 
.. _`credentials/issues/1736`: https://github.com/openedx/credentials/issues/1736 
.. _Django App Plugin: https://github.com/openedx/edx-django-utils/blob/master/edx_django_utils/plugins/README.rst
.. _Django Apps Plugin README: https://github.com/openedx/edx-django-utils/blob/master/edx_django_utils/plugins/README.rst


Decision
--------

* Implement improved plugin support of Django apps in the Credentials service by adopting `edx_django_utils`_ module. Django apps plugins will support `overrides system`_ for core functionality.

* Use plugin applications for future extension points and optional functionality for the Credentials service.

.. _edx_django_utils: https://github.com/openedx/edx-django-utils
.. _overrides system: https://github.com/openedx/edx-django-utils/blob/master/edx_django_utils/plugins/pluggable_override.py#L11

Consequences
------------

* It will be easier to extend the Credentials service and implement new business cases without building a monolithic unit.

* It will be possible to override the core functionality of the Credentials service for specific use cases without direct code modifications.

* It will become easier to support Credentials system "upgradability".

* It may introduce complexity for code discovery in case of implicit overrides and a lack of documentation on particular plugin functionality.

Rejected Alternatives
---------------------

* Adding Django applications directly to credentials/apps.

References
----------

The Open edX platform Django apps ADR 0014: https://github.com/openedx/edx-platform/blob/master/docs/decisions/0014-no-new-apps.rst

How to enable plugins for an IDA: https://github.com/openedx/edx-django-utils/blob/master/edx_django_utils/plugins/docs/how_tos/how_to_enable_plugins_for_an_ida.rst
