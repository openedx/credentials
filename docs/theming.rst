Theming
=======

The base credential template is divided into three customizable sections:

* Header
* Certificate
* Footer

These sections can be customized by creating a theme, and associating that theme with a site/tenant. A theme is simply a
Django app with an assortment of templates. The Open EdX theme (``credentials_theme_openedx``) is included in this
repository as an example.

.. image:: _static/images/theme-sections.png
    :align: center
    :width: 600px
    :alt: Theme sections

Installing a Theme
------------------
Follow the steps below to add a new theme.


1. Install the package into your Python environment (as you would any Django app). If you have setup the app locally, as
   is the case with ``credentials_theme_openedx`` or if you have forked the repo, you are all set.
2. Add the app to the ``INSTALLED_APPS`` setting.
3. Associate the theme with your site by setting the **Theme Name** value at ``/admin/core/siteconfiguration/`` in
   Django admin.
4. Test the setup by rendering the example credential at ``/credentials/example/``. Remember to test all of your program
   types by setting the ``program_type`` parameter to the slugified program type (e.g. "professional-certificate"
   instead of "Professional Certificate").

Creating a Theme
----------------
.. _directory tree example:
.. Generate this with tree (http://mama.indstate.edu/users/ice/tree/), which is available via Homebrew.
.. code-block:: text

    ../credentials/apps/credentials_theme_openedx/
    ├── __init__.py
    ├── locale
    |   ├── en
    │   |   └── LC_MESSAGES
    │   |       └── django.mo
    │   └── es_419
    │       └── LC_MESSAGES
    │           └── django.mo
    ├── static
    │   └── openedx
    │       └── openedx-logo.png
    └── templates
        └── openedx
            ├── _footer.html
            ├── _header.html
            ├── credentials
            │   ├── courses
            │   │   ├── edx+demox
            │   │   │   ├── 4t2017
            │   │   │   │   └── verified
            │   │   │   │       └── certificate.html
            │   │   │   └── certificate.html
            │   │   └── verified
            │   │       └── certificate.html
            │   └── programs
            │       ├── ff51584d-32fa-44b6-b8bb-63a8e55f963a
            │       │   └── certificate.html
            │       └── professional-certificate
            │           └── certificate.html
            └── images
                ├── example-logo.svg
                └── example-watermark.svg

The tree structure above shows the Open EdX theme with overrides for courses and programs.

There are a few notes that theme creators should keep in mind:

1. All directory names, except ``'LC_MESSAGES'``, should be lower-cased to avoid issues that might occur when
   developing on case-insensitive environments (e.g. macOS) and deploying to case-sensitive (e.g. Linux). The
   ``'LC_MESSAGES'`` directory is an exception to this rule, as Django convention requires it to be capitalized. See
   `How Django discovers translations`_ for more information.
2. The rendering view is specifically looking for files named `certificate.html`, `_footer.html`, and `_header.html`.
   If you use different file names for these components, they *will not* be rendered.
3. Feel free to import your custom CSS in `certificate.html`.
4. All theme-related static files and templates should be nested inside a directory with the theme's name (e.g.
   openedx). This will help avoid conflicts with the base templates and, potentially, other apps.
5. Course directories follow the format of {org}+{course}.
6. The `images` directory nested inside `templates` is not a mistake. SVG images can be styled with CSS. This is more
   easily accomplished if the image is inserted via Django's ``{% include %}`` tag rather than loaded as a static file.

Program certificates can be overridden at the following levels:

* Program type
* Individual program (based on UUID)

.. warning::

    Course certificates have not yet been implemented.

Course certificates can be overridden at the following levels:

* Seat type (e.g. honor, professional, verified)
* Course (e.g. edX+DemoX)
* Course run (e.g. course-v1:edX+DemoX+4T2017) + seat type

Internationalization
~~~~~~~~~~~~~~~~~~~~
Strings appearing in overridden files may be marked for translation by wrapping them in Django translation functions.
Refer to the `Django i18n docs`_ for more details.

Translations for custom strings may be provided by including a top-level directory named ``'locale'`` within the theme
application. The ``'locale'`` directory should contain the compiled translation (.mo) files (produced by running the
``django-admin.py compilemessages`` command), and should be structured according to the conventions described in `How
Django discovers translations`_. The `directory tree example`_ provided above includes a properly structured
``'locale'`` directory.

Translations included with the theme application are available to the including application by default. Any conflicts
between translations provided by the theme application and the including application are resolved according to the
precedence rules described in `How Django discovers translations`_.

.. _Django i18n docs: https://docs.djangoproject.com/en/1.11/topics/i18n/translation/#internationalization-in-template-code
.. _How Django discovers translations: https://docs.djangoproject.com/en/1.11/topics/i18n/translation/#how-django-discovers-translations
