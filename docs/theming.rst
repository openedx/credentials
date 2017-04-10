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

.. Generate this with tree (http://mama.indstate.edu/users/ice/tree/), which is available via Homebrew.
.. code-block:: text

    ../credentials/apps/credentials_theme_openedx/
    ├── __init__.py
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

1. All directory names should be lower-cased to avoid issues that might occur when developing on case-insensitive
   environments (e.g. macOS) and deploying to case-sensitive (e.g. Linux).
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
