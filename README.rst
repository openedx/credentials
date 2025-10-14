This is the master branch, which is not used on this fork.

edX Credentials Service |Codecov|_
====================================

.. |Codecov| image:: http://codecov.io/github/edx/credentials/coverage.svg?branch=master
.. _Codecov: http://codecov.io/github/edx/credentials?branch=master

This repository contains the edX Credentials Service, which supports course and program certificates. This service is a
replacement for the ``certificates`` app in ``edx-platform``.

Credentials can be run as part of devstack_ or Tutor_ (using the tutor_credentials_ plugin).

.. _devstack: https://github.com/openedx/devstack
.. _tutor: https://docs.tutor.edly.io/
.. _tutor_credentials: https://github.com/overhangio/tutor-credentials

Where to run `make` commands
--------------------------

Due to the nature of developing in containers, some commands must be ran inside the container. Currently most commands
can be ran either inside the container or inside a local virtual environement, once developer requirements have been
installed (using the `make requirements` target).

Frontend Development
--------------------

The `Learner Record`_ feature and frontend components have been extracted into a dedicated MFE.

When developing frontend code in Credentials, some of the code must be transpiled and bundled for it to be usable. The
SASS code found in the ``credentials/static/sass`` directory of this project.

In order to view your changes, you must run one of the `make static` commands. `make static` builds and collects your
static assets once, while `make static.watch` will continue to watch for changes in your code and rebuild/recollect
whenever you save. When using `make static.watch` it only triggers after save, so if you have existing changes, you
need to run `make static` once first, or make a small change to an existing file and save it so it triggers a rebuild.

To see changes locally, from your devstack repo run ::

  make credentials-shell
  make static
  make static.watch

.. _Learner Record: https://github.com/openedx/frontend-app-learner-record

Testing
-------

In order for developers to have a consistent experience between CI and local testing, we are using a locally built
container image that mimics the ones that Github Actions uses.

NOTE: The first time you run any of the test suites below, it will build the image which will take a few minutes.
Following test runs will be quicker.

To run python and javascript tests locally ("unit_tests" in CI) ::

  make unit_tests_suite

To run quality and translation tests locally ("quality_and_translations_tests" in CI) ::

  make quality_and_translations_tests_suite

isort and formatting (`black`) quality issues can be fixed automatically by running either ::

  make isort
  # or
  make format

Documentation
-------------

`Documentation`_ is hosted on Read the Docs. The source is hosted in this repo's `docs`_ directory. To contribute,
please open a PR against this repo.

.. _Documentation: https://edx-credentials.readthedocs.io/en/latest/
.. _docs: https://github.com/openedx/credentials/tree/master/docs

License
-------

The code in this repository is licensed under version 3 of the AGPL unless otherwise noted. Please see the LICENSE_ file
for details.

.. _LICENSE: https://github.com/openedx/credentials/blob/master/LICENSE

How To Contribute
-----------------

Contributions are welcome. Please read `How To Contribute`_ for details.

.. _`How To Contribute`: https://github.com/openedx/.github/blob/master/CONTRIBUTING.md

Reporting Security Issues
-------------------------

Please do not report security issues in public. Please email security@openedx.org.

Get Help
--------

If you're having trouble, we have `discussion forums`_ where you can connect with others in the community.

Our real-time conversations are on Slack_.

.. _`discussion forums`: https://discuss.openedx.org
.. _Slack: http://openedx.slack.com/
