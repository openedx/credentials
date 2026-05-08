.. _badges-configuration:

Badging Configuration
=====================

Badge templates, requirements, data rules, and penalties are configured in the Badges section of the Credentials administration panel.
Each badge template needs at least one requirement and must be activated before it takes effect.

The screenshot below shows the main admin entry point where you access provider records, badge templates, requirements, penalties, and issued badge data.

.. figure:: ../../../_static/images/badges/badges-admin.png
   :alt: Credentials Django admin index showing the Badges section where badge templates, requirements, and provider records are managed.

Provider Setup
--------------

Use the provider-specific pages in this section when you need to configure provider credentials, synchronize badge templates or groups, or understand provider-specific behavior such as webhooks and synchronization rules.

.. toctree::
   :maxdepth: 1

   credly
   accredible
   examples

.. _badges-configuration-templates:

Badge Templates
---------------

Credentials stores provider-side badge definitions as badge templates.
Credly exposes them as badge templates at ``https://<your-credentials-host>/admin/badges/credlybadgetemplate/``.
Accredible exposes the equivalent records as groups at ``https://<your-credentials-host>/admin/badges/accrediblegroup/``.

Open the template or group record to review and update badge configuration.
This detail page is where you manage provider-specific attributes, requirements, penalties, and activation state.

The screenshot below shows the badge template detail page used to review badge-specific configuration.

.. figure:: ../../../_static/images/badges/badges-admin-template-details.png
   :alt: Badge template detail page showing the sections used to review badge-specific configuration.

The badge template detail page contains the following sections:

.. list-table:: Badge template detail page sections
   :widths: 30 70
   :header-rows: 1

   * - Section
     - Description
   * - Generic
     - Shared settings such as site assignment and activation state.
   * - Badge template
     - Badge-specific fields such as name, description, image, and origin. These values are populated from the remote provider during synchronization.
   * - Credly or Accredible
     - Provider-managed fields such as state, dashboard link, and organization or API configuration. The section label depends on the provider. See :ref:`badges-credly-configuration` or :ref:`badges-accredible-configuration`.
   * - Configured requirements
     - Inline requirement records for this badge template. See :ref:`badges-configuration-requirements`.
   * - Configured penalties
     - Inline penalty records for this badge template. See :ref:`badges-configuration-penalties`.

.. _badges-configuration-requirements:

Badge Requirements
------------------

Requirements describe what must happen for a learner to earn a badge.
At least one requirement must be associated with a badge template.
A badge template can have multiple requirements, and **all requirements** must be fulfilled before the system issues a badge.
The badge template must be activated before it takes effect.

The screenshot below shows the inline badge requirements section on the badge template detail page.

.. figure:: ../../../_static/images/badges/badges-admin-template-requirements.png
   :alt: Badge template detail page showing the inline list of badge requirements beneath the template record.

Each requirement has the following fields.

- **Event type** - the Open edX platform event that must occur. The default supported events are:

  - ``org.openedx.learning.course.passing.status.updated.v1`` - course grade updated.
  - ``org.openedx.learning.ccx.course.passing.status.updated.v1`` - CCX course grade updated.

  Any public signal from the `openedx-events`_ library can extend this set (see :ref:`badges-settings`).
- **Rules** - a list of configured data rules (if any). See :ref:`badges-configuration-data-rules`.
- **Description** - an optional human-readable reminder about the requirement's purpose.
- **Group** - controls OR/AND behavior across requirements. See :ref:`badges-configuration-groups`.

.. figure:: ../../../_static/images/badges/badges-admin-template-requirements.png
   :alt: Badge template detail page showing the inline list of badge requirements beneath the template record.

.. note::

   You can use any public signal from the `openedx-events`_ library if its payload includes learner-identifying PII in ``UserData``.

.. _badges-configuration-groups:

Badge Requirement Groups
------------------------

Each requirement has a **Group** field. In the admin, you select one of the available group values from ``A`` to ``Z``. New requirements default to the next available letter.

Requirements in the same group use OR logic - fulfilling any one of them fulfills the group.
Requirements in different groups use AND logic - all groups must be fulfilled before the badge is issued.

Use groups when a learner can satisfy one part of a badge in multiple ways.
For example, if a learner may complete either Course A or Course B to satisfy one part of a badge, place both requirements in the same group.
If the learner must also complete Course C, put that requirement in a separate group.

For example:

- Group ``A``

  - Requirement 1: pass Course A
  - Requirement 2: pass Course B

- Group ``B``

  - Requirement 3: pass Course C

In this configuration, the learner must fulfill either Requirement 1 or Requirement 2, and also fulfill Requirement 3.

The screenshot below continues the requirement form and highlights the **Group** field.

.. figure:: ../../../_static/images/badges/badges-admin-rules-group.png
   :alt: Badge requirement form showing the Group field used to place multiple requirements into the same OR-logic group.

For more grouping examples, see :ref:`Configuration examples for Badging`.

.. _badges-configuration-data-rules:

Data Rules
----------

Data rules narrow a single badge requirement by constraining what event payload values count as a match.
Multiple data rules on one requirement all must match (AND logic).
Data rules do not link requirements together - each rule set applies only to its own requirement's incoming event.

Data rules are configured on the badge requirement detail page, not on the badge template page.
The requirement detail page is opened from the inline requirements list on a badge template or group record, and the direct admin URL pattern is ``https://<your-credentials-host>/admin/badges/badgerequirement/<id>/change/``.

To add or edit a data rule:

#. Navigate to ``https://<your-credentials-host>/admin/badges/credlybadgetemplate/`` or ``https://<your-credentials-host>/admin/badges/accrediblegroup/`` and open the template or group you want to configure.
#. In the inline requirements list, use the ``Change`` link for the requirement you want to edit.
#. On the requirement detail page, find the "Data Rules" section and add a new item.

.. figure:: ../../../_static/images/badges/badges-admin-requirement-rules.png
   :alt: Badge requirement detail form opened from the inline Change link, showing where Data Rules are configured for that requirement.

Each data rule describes a single expected payload value.
Key paths are generated from the event type of the parent requirement.

.. figure:: ../../../_static/images/badges/badges-admin-data-rules.png
   :alt: Badge requirement form showing the inline Data Rules section with numbered markers for key path, operator, and expected value fields.

The numbered markers on the screenshot correspond to data rule fields:

.. list-table::
   :widths: 10 20 70
   :header-rows: 1

   * - #
     - Field
     - Description
   * - 1
     - **Key path**
     - Dot-separated path to a field in the event payload. Available key paths depend on the selected event type and come from the event structure defined in `openedx-events`_.
   * - 2
     - **Operator**
     - Comparison operation: ``"="`` (equals) or ``"!="`` (not equals).
   * - 3
     - **Expected value**
     - The expected value of that event field, for example ``true``, ``course-v1:OpenedX+DemoX+Demo_Course``, or ``ccx-v1:edX+DemoX+Demo_Course+ccx@1``.

.. note::

   For boolean fields, the following string values are accepted:

   - **True:** ``"true"``, ``"True"``, ``"yes"``, ``"Yes"``, ``"+"``
   - **False:** ``"false"``, ``"False"``, ``"no"``, ``"No"``, ``"-"``

For complete requirement and data rule configurations, see :ref:`Configuration examples for Badging`.

.. _badges-configuration-penalties:

Badge Penalties
---------------

Badge penalties reset learner progress when a specific event occurs.
Use them for cases where previously earned progress should no longer count, for example when a passing grade later changes to failing.
For details on how this leads to badge revocation during processing, see :ref:`badges-processing`.

Penalties are optional. A badge template can have zero or more penalties.

Configure penalties on the badge template or group detail page through the inline penalty records.
Open the template record from ``https://<your-credentials-host>/admin/badges/credlybadgetemplate/`` or the group record from ``https://<your-credentials-host>/admin/badges/accrediblegroup/``, then use the inline penalty records.
Penalty detail pages use the admin URL pattern ``https://<your-credentials-host>/admin/badges/badgepenalty/<id>/change/``.

A penalty is configured with an :ref:`event type <badges-configuration-requirements>`, its own :ref:`data rules <badges-configuration-data-rules>`, and one or more linked :ref:`badge requirements <badges-configuration-requirements>`.
When an incoming event matches all of the penalty's data rules, the linked requirements are reset for that learner.

.. figure:: ../../../_static/images/badges/badges-admin-penalty-rules.png
   :alt: Badge penalty form showing the event trigger, linked requirements, and data rules used to reset learner progress.

For example, the penalty shown in the screenshot above could listen for a ``course.passing.status.updated`` event where ``is_passing`` equals ``false``.
If that event occurs, the learner's progress for the linked requirements is reset.

Examples
--------

Use :ref:`Configuration examples for Badging` for complete requirement and data rule configurations for common badge setups.

.. _badges-configuration-activation:

Activation and Deactivation
---------------------------

Use the badge template or group detail page to activate or deactivate badge processing for a template.

#. Navigate to ``https://<your-credentials-host>/admin/badges/credlybadgetemplate/`` or ``https://<your-credentials-host>/admin/badges/accrediblegroup/``.

   .. figure:: ../../../_static/images/badges/badges-admin-credly-templates-list.png
      :alt: Badge templates list page in the Credentials admin.

#. Open the badge template or group detail page and set the ``Is active`` checkbox as needed.

   .. figure:: ../../../_static/images/badges/badges-admin-activation.png
      :alt: Badge template detail page showing the Is active checkbox.

#. Click **Save**.

.. important::

   After you activate a badge template, matching incoming events can fulfill its requirements, update learner progress, and trigger badge issuance when all required conditions are met.

   Deactivating a badge template stops future processing for that template. Already issued badges are retained.
   Inactive badge templates are ignored during event processing.

.. _openedx-events: https://github.com/openedx/openedx-events
