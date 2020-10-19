edX Credentials Service  |Travis|_ |Codecov|_
=============================================
.. |Travis| image:: https://travis-ci.com/edx/credentials.svg?branch=master
.. _Travis: https://travis-ci.com/edx/credentials

.. |Codecov| image:: http://codecov.io/github/edx/credentials/coverage.svg?branch=master
.. _Codecov: http://codecov.io/github/edx/credentials?branch=master

This repository contains the edX Credentials Service, which supports course and program certificates. This service is a replacement for the ``certificates`` app in ``edx-platform``.

Documentation
-------------

`Documentation`_ is hosted on Read the Docs. The source is hosted in this repo's `docs`_ directory. To contribute, please open a PR against this repo.

.. _Documentation: https://edx-credentials.readthedocs.io/en/latest/
.. _docs: https://github.com/edx/credentials/tree/master/docs

License
-------

The code in this repository is licensed under version 3 of the AGPL unless otherwise noted. Please see the LICENSE_ file for details.

.. _LICENSE: https://github.com/edx/credentials/blob/master/LICENSE

How To Contribute
-----------------

Contributions are welcome. Please read `How To Contribute`_ for details. Even though it was written with ``edx-platform`` in mind, these guidelines should be followed for Open edX code in general.

.. _`How To Contribute`: https://github.com/edx/edx-platform/blob/master/CONTRIBUTING.rst

Reporting Security Issues
-------------------------

Please do not report security issues in public. Please email security@edx.org.

Testing
-------

The command below runs all of the Python and JS tests::

  $ make tests

The Python tests can be run independently with::

  $ pytest --ds credentials.settings.test

If this is the first time you've run tests, you'll have to run::

  $ make static

first, otherwise you'll run into ``webpack_loader.exceptions.WebpackBundleLookupErrors``.

Get Help
--------

If you're having trouble, we have `discussion forums`_ where you can connect with others in the community.

Our real-time conversations are on Slack_.

.. _`discussion forums`: https://discuss.openedx.org
.. _Slack: http://openedx.slack.com/
