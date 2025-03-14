Internationalization
====================
Follow the `internationalization coding guidelines`_ in the edX Developer's Guide when developing new features.

Generally, all user facing text should be wrapped in Django translation functions so that the strings can be extracted
and translated. Refer to the `Django internationalization documentation`_ for more details.

.. contents::
  :local:
  :depth: 1

Language Resolution
~~~~~~~~~~~~~~~~~~~
By default, all certificates are rendered in the application's default language (defined by the `LANGUAGE_CODE
setting`_).

Program certificates that use a ``ProgramCertificate`` configuration that has been associated with a
specific language are rendered in that language. Program certificates that use a ``ProgramCertificate`` configuration
that has **not** been associated with a specific language are rendered in the application's default language.

LMS and browser language preference settings are not used when rendering certificates.

Internationalized Program Certificates
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
Program certificates can be configured to render in a specific language by following these steps.

#. Configure the ``CERTIFICATE_LANGUAGES`` setting (in your Django settings file) with at least one language. This
   setting is used to specify the languages that can be used to render certificates. It should be defined as a
   dictionary in the format ``{language_code: language_display_name}``, where language_code is a supported application
   language code (as described in the `Django docs for language_code`_) and ``language_display_name`` is the text that
   is used to represent that language in the Django admin UI.

   For example:

   .. code-block:: python

     CERTIFICATE_LANGUAGES = {
       'en': 'English',
       'es': 'Spanish',
       'es-419': 'Spanish (Latin American)'
     }

#. Log in to the Django admin for your Credentials instance (``{credentials_base_url}/admin``).

#. Navigate to the **Program certificate configurations** admin page (``{credentials_base_url}/admin/credentials/programcertificate/``).

#. Select the **Program certificate configuration instance** for the program that you want to have rendered in a
   specific language (or click **Add Program certificate configuration** in the top right corner of the page to add a
   new one).

#. On the **Change Program certificate configuration** (or **Add Program certificate configuration**) page, fill in the
   ``language`` field by selecting a language from the dropdown (which is populated from the entries in
   ``CERTIFICATE_LANGUAGES``) and click **Save**. Program certificates that use this configuration will now render using
   this language.

Translation Management
~~~~~~~~~~~~~~~~~~~~~~
Translations need to be updated whenever user facing text is added or changed in the repository. This is typically
done in three steps. If you are a developer using docker and you are trying to update translations, please see the
next section.

#. Extract strings that have been marked for translation into message `(.po) files`_. This can be done by running
   the Django `makemessages`_ command, which will create or update message (.po) files for each specified locale
   and store them in ``credentials/conf/locale/<language_code>/LC_MESSAGES/``.

#. Fill in the message (.po) files with the appropriate metadata and translations. Look out for `Fuzzy entries`_
   (entries marked with ``#, fuzzy``), which indicate that the existing translations are no longer exact matches.
   The translations for these entries should be checked for accuracy and updated if necessary. Be sure to remove
   the ``#, fuzzy`` tag once you've verified or fixed a fuzzy translation. Message (.po) files containing fuzzy
   translations will still compile, but any entries marked with a ``#, fuzzy`` tag will not be available in the
   application.

#. Compile the message (.po) files into `(.mo) files`_. This can be done by running the Django
   `compilemessages`_ command. This is necessary because the (.mo) files are what Django actually uses to load
   translations for the application.

For more information about translation management, please refer to the `Django internationalization documentation`_.

Note: We also rely on Django's extraction for js/jsx files as well.  Since Django's extraction does not support es6 (more specifically template literals), we have temporarily disallowed using this feature via an eslint rule.

Translation Management with Docker
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
If you are using docker and you have added or changed user facing text in the repository, you can update or change
translations using the following steps and commands that are provided in the credentials ``Makefile``.

#. Make sure to stage your changes that need to be committed.

#. Extract the messages, generate and compile the dummy translations, and verify that the translation files are
   up-to-date. This can be done by running the following command:

   .. code-block:: bash

      $ make check_translations_up_to_date


#. Finally, stage your updated translation files to be committed with the rest of your work.

.. _internationalization coding guidelines: https://docs.openedx.org/en/latest/developers/references/developer_guide/internationalization/i18n.html
.. _Django internationalization documentation: https://docs.djangoproject.com/en/1.11/topics/i18n
.. _LANGUAGE_CODE setting: https://docs.djangoproject.com/en/1.11/ref/settings/#language-code
.. _Django docs for language_code: https://docs.djangoproject.com/en/1.11/topics/i18n/#term-language-code
.. _(.po) files: https://www.gnu.org/software/gettext/manual/html_node/PO-Files.html
.. _makemessages: https://docs.djangoproject.com/en/1.11/ref/django-admin/#makemessages
.. _(.mo) files: https://www.gnu.org/software/gettext/manual/html_node/MO-Files.html
.. _compilemessages: https://docs.djangoproject.com/en/1.11/ref/django-admin/#compilemessages
.. _Fuzzy entries: https://www.gnu.org/software/gettext/manual/html_node/Fuzzy-Entries.html
