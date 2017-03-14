Asset Pipeline
==============

Static files are managed via  `webpack <https://webpack.github.io/>`_ and
`django-webpack-loader <https://github.com/owais/django-webpack-loader>`_.

There are a few `make` targets to aid asset compilation:

+--------------+-------------------------------------------------------------------------------+
| Target       | Description                                                                   |
+==============+===============================================================================+
| static       | Compile and minify all static assets. (Use this for production.)              |
+--------------+-------------------------------------------------------------------------------+
| static.dev   | Compile all static assets, but do NOT minify.                                 |
+--------------+-------------------------------------------------------------------------------+
| static.watch | Same as `static.dev`, but assets are compiled whenever a source file changes. |
+--------------+-------------------------------------------------------------------------------+

.. note::

    If you need to remove all *compiled and collected* static assets, run ``make clean_static``.

When adding new modules/pages that require custom CSS or JavaScript, remember to add a new entrypoint to
``webpack.config.js``.
