Managing Badges
===============

Creating Provider-Side Badge Definitions
----------------------------------------

Before you can synchronize or activate badges in Open edX Credentials, you must create the provider-side badge definitions in Credly or Accredible.

For **Credly**:

- Create and publish badge templates in your Credly organization first.
- Then configure the organization in Open edX Credentials and synchronize templates. See :ref:`badges-credly-configuration`.

For **Accredible**:

- Create groups in Accredible first.
- Then configure the API connection in Open edX Credentials and synchronize groups. See :ref:`badges-accredible-configuration`.

Synchronizing Badge Templates
-----------------------------

Badge templates (Credly) and groups (Accredible) are created on the provider's side and then pulled into Open edX Credentials through a sync action in the admin panel.

For **Credly**:

#. Navigate to ``https://<your-credentials-host>/admin/badges/credlyorganization/`` and select one or more organizations.
#. Run the ``Sync organization badge templates`` action.

   .. figure:: ../../_static/images/badges/badges-admin-credly-templates-sync.png
      :alt: Credly Organizations admin list showing the sync badge templates action.

Only badge templates with ``active`` state on Credly are pulled. See :ref:`badges-credly-configuration` for webhook setup and full sync details.

For **Accredible**:

#. Navigate to ``https://<your-credentials-host>/admin/badges/accredibleapiconfig/`` and select one or more configurations.
#. Run the ``Sync groups`` action.

   .. figure:: ../../_static/images/badges/badges-admin-groups-sync.png
      :alt: Accredible API Configs admin list showing the sync groups action.

See :ref:`badges-accredible-configuration` for full sync details.

.. note::

   Synchronized templates and groups are created **inactive** by
   default. Configure requirements and activate them before they
   take effect. See :ref:`badges-configuration-activation`.

Badge Progress
--------------

Current badge progress is visible at ``https://<your-credentials-host>/admin/badges/badgeprogress/`` in the Credentials admin.

Badge templates can have more than one requirement, so there can
be partially completed badges. See :ref:`badges-processing` for
details on how progress is tracked.

Awarded Credentials
-------------------

Earned badges are listed at ``https://<your-credentials-host>/admin/badges/credlybadge/`` for Credly and ``https://<your-credentials-host>/admin/badges/accrediblebadge/`` for Accredible.

Once badge progress is complete (all requirements are *fulfilled*),
the system awards the badge. See :ref:`badges-processing` for the
full awarding pipeline.

The system:

#. Creates an internal user credential record for the learner.
#. Emits a public signal about the badge award.
#. Sends an API request to the badge provider to issue the badge externally.

Issued Badges
-------------

After a badge is awarded internally, the system sends an API request to
the badge provider to issue the badge on their platform.

On successful issuing, the badge record in ``https://<your-credentials-host>/admin/badges/credlybadge/`` or ``https://<your-credentials-host>/admin/badges/accrediblebadge/`` is updated with:

#. **External identifier** - the identifier assigned by the provider (UUID for Credly, integer ID for Accredible).
#. **External state** - the badge status on the provider's side (e.g. ``accepted``).

The issued badge then appears in the provider's dashboard and is visible
to the learner.

Deactivation
------------

Deactivating a badge template stops future processing for that template. Already issued badges are retained.

Deactivate a badge template by opening the record from ``https://<your-credentials-host>/admin/badges/credlybadgetemplate/`` or ``https://<your-credentials-host>/admin/badges/accrediblegroup/``, unchecking ``Is active``, and clicking **Save**.

Inactive badge templates are ignored during event processing. To reactivate, check ``Is active`` again and save - processing resumes for new events immediately.

See :ref:`badges-configuration-activation` for activation details.

.. seealso::

   `Credly Knowledge Base <https://support.credly.com/hc/en-us>`_
      Provider-side setup and management for Credly badge templates.

   `Accredible Help Center <https://help.accredible.com/>`_
      Provider-side setup and management for Accredible groups.

   :ref:`badges-configuration`
      Configure badge templates, requirements, and data rules.

   :ref:`badges-settings`
      Feature switches and integration settings.

   :ref:`badges-processing`
      How incoming events are processed and badges are awarded.
