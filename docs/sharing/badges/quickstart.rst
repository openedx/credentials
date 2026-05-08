.. _badges-quickstart:

Quick Start
===========

Set up badge issuing for your Open edX instance with Credly or Accredible. By the end of this guide you will have a working badge template that awards badges to learners automatically.

.. contents:: Steps
    :local:
    :class: no-bullets

1. Prerequisites and installation
---------------------------------

The Credentials service must be installed and running on your Open edX instance.

Option A: Using Tutor (recommended)
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

#. Install the `tutor-credentials`_ plugin (provides the Credentials service):

   .. code-block:: bash

       pip install tutor-credentials

#. Install the `tutor-contrib-badges`_ plugin (configures badge settings, event bus, and feature flags automatically):

   .. code-block:: bash

       pip install git+https://github.com/raccoongang/tutor-contrib-badges@main

   See the `tutor-contrib-badges README <https://github.com/raccoongang/tutor-contrib-badges#readme>`_ for additional details, including a sample Pipfile and manual service commands.

#. Enable the necessary plugins:

   .. code-block:: bash

       tutor plugins enable discovery mfe credentials badges

#. Rebuild images and launch:

   .. code-block:: bash

       tutor images build openedx discovery credentials
       tutor local launch

The plugin automatically enables badge feature flags, configures the event bus, and registers the following consumer services:

- ``credentials-eventbus-consumer``
- ``credentials-certificates-eventbus-consumer``
- ``lms-eventbus-consumer``
- ``cms-eventbus-consumer``


.. _tutor-credentials: https://github.com/overhangio/tutor-credentials
.. _tutor-contrib-badges: https://github.com/raccoongang/tutor-contrib-badges

Option B: Other installations
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

#. Install the Credentials service following the `Getting Started <https://edx-credentials.readthedocs.io/en/latest/getting_started.html>`_ guide.

#. Enable badges in both services:

   .. code-block:: python

       # openedx-platform (LMS) settings:
       FEATURES["BADGES_ENABLED"] = True

       # Credentials service settings:
       BADGES_ENABLED = True

#. Configure the event bus and consumer processes. See :ref:`badges-settings` for the full reference:

   - :ref:`badges-event-bus-configuration` - producer signals for LMS and Credentials.
   - :ref:`badges-consumer-setup` - running the ``consume_events`` management command.

.. _quickstart-configure-integration:

2. Configure integration
------------------------

Set up your provider account and connect it to the Credentials admin panel for your instance.

For **Credly**:

#. Register on `Credly <https://info.credly.com/>`_ and create your organization.
#. Create at least one badge template and publish it.
#. Retrieve your organization UUID and `API key <https://credlyissuer.zendesk.com/hc/en-us/articles/28143019451035-Auth-tokens-for-authorization>`_.
#. In the Credentials admin panel, navigate to ``https://<your-credentials-host>/admin/badges/credlyorganization/`` and add a new organization.

   a. Set the **UUID** to your Credly organization identifier.
   b. Set the **API key** used to authenticate with the Credly organization.

   .. figure:: ../../_static/images/badges/badges-admin-credly-organization.png
      :alt: Add Credly organization form showing the Uuid and Api key fields.

#. Verify the system pulls the organization's data and updates its name.


For **Accredible**:

#. Register on `Accredible <https://www.accredible.com/>`_ and create your account.
#. Create at least one group.
#. Retrieve your `API key <https://help.accredible.com/s/article/how-do-i-find-my-integration-api-key?language=en_US>`_ from account settings.
#. In the Credentials admin panel, navigate to ``https://<your-credentials-host>/admin/badges/accredibleapiconfig/`` and add a new configuration.

   a. Set the **API key** from your Accredible account.
   b. Set a **name** for the configuration.

   .. figure:: ../../_static/images/badges/badges-admin-accredible-api-config.png
      :alt: Add Accredible API config form showing the Name and Api key fields.


.. seealso::

   **Credly**

   :ref:`badges-credly-configuration`
      Full Credly setup, webhooks, and synchronization details.

   `Credly Authentication Methods <https://docs.credly.com/browse/docs/authentication-methods>`_
      How to authenticate with the Credly API.

   `Auth Tokens for Authorization <https://credlyissuer.zendesk.com/hc/en-us/articles/28143019451035-Auth-tokens-for-authorization>`_
      How to generate and manage Credly auth tokens.

   **Accredible**

   :ref:`badges-accredible-configuration`
      Full Accredible setup and synchronization details.

   `How Do I Find My Integration API Key? <https://help.accredible.com/s/article/how-do-i-find-my-integration-api-key?language=en_US>`_
      Finding your Accredible API key for integration setup.

3. Synchronize badge templates
------------------------------

Synchronization imports badge templates from your provider into the Credentials service.

For **Credly**:

#. Navigate to ``https://<your-credentials-host>/admin/badges/credlyorganization/`` and select the organization(s) you want to use.
#. Run the ``Sync organization badge templates`` action.

   .. figure:: ../../_static/images/badges/badges-admin-credly-templates-sync.png
      :alt: Credly Organizations admin list showing the sync badge templates action.

#. Navigate to ``https://<your-credentials-host>/admin/badges/credlybadgetemplate/`` and verify the newly created templates.

See :ref:`badges-credly-configuration` for details on template synchronization and webhook setup.

For **Accredible**:

#. Navigate to ``https://<your-credentials-host>/admin/badges/accredibleapiconfig/`` and select the configuration(s) you want to use.
#. Run the ``Sync groups`` action.

   .. figure:: ../../_static/images/badges/badges-admin-groups-sync.png
      :alt: Accredible API Configs admin list showing the sync groups action.

#. Navigate to ``https://<your-credentials-host>/admin/badges/accrediblegroup/`` and verify the newly created groups.

See :ref:`badges-accredible-configuration` for details on group synchronization.

4. Set up badge requirements
----------------------------

Requirements define what must happen for a learner to earn a badge. At least one requirement must be associated with a badge template.

In the Credentials admin panel, open the badge template or group record you want to configure from ``https://<your-credentials-host>/admin/badges/credlybadgetemplate/`` or ``https://<your-credentials-host>/admin/badges/accrediblegroup/``:

.. figure:: ../../_static/images/badges/badges-admin-template-requirements.png
   :alt: Badge template detail page showing the inline list of badge requirements.

#. Find the "Badge Requirements" section.
#. Add a new item and select an event type (what is expected to happen).

   - Optionally, add a description.

#. Save and navigate to the requirement detail page by using the ``Change`` link in the inline requirements list. Requirement detail pages use the admin URL pattern ``https://<your-credentials-host>/admin/badges/badgerequirement/<id>/change/``.

   - Optionally, specify data rules in the "Data Rules" section:

     #. Select a key path (specific data element).
     #. Select an operator (how to compare the value).
     #. Enter a value (expected parameter's value).

.. figure:: ../../_static/images/badges/badges-admin-data-rules.png
   :alt: Badge requirement form showing the inline Data Rules section.

A badge template can have more than one requirement. For example, a badge
template issued on a specific course completion:

- Requirement 1:
    - event type: ``org.openedx.learning.course.passing.status.updated.v1``
    - description: ``On the Demo course completion.``
- Data rule 1:
    - key path: ``course.course_key``
    - operator: ``"=" (equals)``
    - value: ``course-v1:OpenedX+DemoX+Demo_Course``
- Data rule 2:
    - key path: ``is_passing``
    - operator: ``"=" (equals)``
    - value: ``true``

.. seealso::

   :ref:`badges-configuration-requirements`
      Full reference for badge requirements.

   :ref:`badges-configuration-data-rules`
      Full reference for data rules.

5. Activate badge templates
---------------------------

#. Navigate to ``https://<your-credentials-host>/admin/badges/credlybadgetemplate/`` or ``https://<your-credentials-host>/admin/badges/accrediblegroup/``.

   .. figure:: ../../_static/images/badges/badges-admin-credly-templates-list.png
      :alt: Badge templates list page in the Credentials admin.

#. Open the badge template or group detail page and check the ``Is active`` checkbox.

   .. figure:: ../../_static/images/badges/badges-admin-activation.png
      :alt: Badge template detail page showing the Is active checkbox.

#. Click **Save**.

.. warning::

    Changing configuration of active badge templates may cause inconsistent learner experience.

.. seealso::

   :ref:`badges-configuration-activation`
      Full reference for badge template activation.
