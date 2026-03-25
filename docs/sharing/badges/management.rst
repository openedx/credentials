Managing Badges
===============

Synchronizing Badge Templates
-----------------------------

Badge templates (Credly) and groups (Accredible) are created on the
provider's side and then pulled into the Credentials service through a
sync action in the admin panel.

For **Credly**:

#. Select one or more organizations on the "Credly Organizations" list page.
#. Run the ``Sync organization badge templates`` action.

Only badge templates with ``active`` state on Credly are pulled.
See :ref:`badges-credly-configuration` for details.

For **Accredible**:

#. Select one or more configurations on the "Accredible API Configs" list
   page.
#. Run the ``Sync groups`` action.

See :ref:`badges-accredible-configuration` for details.

.. note::

   Synchronized templates and groups are created **inactive** by
   default. Configure requirements and activate them before they
   take effect. See :ref:`badges-configuration-activation`.

Badge Progress
--------------

Current badge progress is visible in the "Badge progress records"
section of the Credentials admin panel.

Badge templates can have more than one requirement, so there can
be partially completed badges. See :ref:`badges-processing` for
details on how progress is tracked.

Awarded Credentials
-------------------

Earned badges are listed in the provider-specific section of the admin panel.

.. note::

    Each badge is an extended version of a user credential record.

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

On successful issuing, the badge record in the admin panel is updated with:

#. **external UUID** - the identifier assigned by the provider.
#. **external state** - the badge status on the provider's side
   (e.g. ``accepted``).

The issued badge then appears in the provider's dashboard and is visible
to the learner.

Badge Template Withdrawal
-------------------------

Deactivate a badge template by unchecking the ``is active`` checkbox
on its edit page. See :ref:`badges-configuration` for activation details.

Inactive badge templates are ignored during processing.

.. seealso::

   :ref:`badges-configuration`
      Configure badge templates, requirements, and data rules.

   :ref:`badges-settings`
      Feature switches and integration settings.

   :ref:`badges-processing`
      How incoming events are processed and badges are awarded.
