Testing
=======

In order for developers to have a consistent experience between CI and local testing, we are using a locally built
container image that mimics the ones that Github Actions uses.

NOTE: The first time you run any of the test suites below, it
will build the image which will take a few minutes. Following test runs will be quicker.

To make testing easier, there are a few commands that mirror our suites in CI:

.. code-block:: bash

    $ make unit_tests_suite
    $ make quality_and_translations_tests_suite

This will run the Python, the Javascript tests, and our quality and translation suite, respectively.


Writing Python Tests
--------------------
Tests should be written for all new features. The `Django docs`_ are a good resource for learning how to test Django code.

.. _Django docs: https://docs.djangoproject.com/en/1.11/topics/testing/


Writing JS tests
----------------
All new front-end features should be made with React, subsequently, all tests written for those features should use the Jest testing framework.


Autoformatting
--------------
All code must be autoformatted or it will fail quality checks. All you need to do to autoformat your PR is run `make format`.
