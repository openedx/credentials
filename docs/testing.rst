Testing
=======

All the below commands should be run from inside the credentials container.

The command below runs all of the Python and JS tests:

.. code-block:: bash

    $ make tests

Acceptance tests can be run like so:

.. code-block:: bash

    $ make accept

Code quality validation (e.g. linters) can be run independently with:

.. code-block:: bash

    $ make quality

The Python tests can be run independently with:

.. code-block:: bash

    $ pytest --ds credentials.settings.test

The react js tests can be run independently with:

.. code-block:: bash

    $ make test-react

The js quality tests can be run independently with:

.. code-block:: bash

    $ make quality-js


Writing Python Tests
--------------------
Tests should be written for all new features. The `Django docs`_ are a good resource for learning how to test Django code.

.. _Django docs: https://docs.djangoproject.com/en/1.11/topics/testing/


Writing JS tests
----------------
All new front-end features should be made with React, subsequently, all tests written for those features should use the Jest testing framework.
