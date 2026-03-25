Quick Start
===========

.. note::

   Open edX supports two badge providers: Credly and Accredible. Both use the same concept - a **badge template** defines the badge design and awarding rules. Credly calls these "badge templates"; Accredible calls them "groups." This guide uses "badge template" as the generic term.

.. contents:: Steps
    :local:
    :class: no-bullets

Prerequisites
-------------

To start using this feature a Credly or Accredible account is necessary.

For Credly:

#. Register on Credly and create your account.
#. Create Organization in Credly.
#. Create at least 1 badge template and activate it.

For Accredible:

#. Register on Accredible and create your account.
#. Create at least 1 group.

1. Enable badges
----------------

Badges feature is optional and disabled by default. Enable it in both services.

.. code-block:: python

    # openedx-platform (LMS) settings:
    FEATURES["BADGES_ENABLED"] = True

    # Credentials service settings:
    BADGES_ENABLED = True

2. Configure integration
------------------------

Go to the Credentials service admin panel and configure the integration.

For **Credly**:

#. Go to ``<credentials>/admin/badges/credlyorganization/`` to add Credly Organization.

   a. Add UUID (unique identifier) for the Credly organization.
   b. Add the authorization token of the Credly organization.

#. Verify the system pulls the Organization's data and updates its name.

For **Accredible**:

#. Retrieve API Key from Accredible account settings (Manage API Keys).
#. Go to ``<credentials>/admin/badges/accredibleapiconfig/`` to add Accredible configuration.

   a. Add API Key.
   b. Add name for configuration.

See :ref:`badges-configuration` for details.

3. Synchronize badge templates
------------------------------

For **Credly**:

#. From the "Credly Organizations" list, select the Organization(s) you want to use.
#. Run the ``Sync organization badge templates`` action.
#. Navigate to the "Credly badge templates" list and verify the newly created templates.

For **Accredible**:

#. From the "Accredible API Configurations" list, select the Configuration(s) you want to use.
#. Run the ``Sync groups`` action.
#. Navigate to the "Accredible groups" list and verify the newly created groups.

4. Setup badge requirements
---------------------------

Requirements describe what and how something must happen on the system to
earn a badge. At least one requirement must be associated with a badge
template. In the Credentials admin panel, open the badge template details
page:

#. Find the "Badge Requirements" section.
#. Add a new item and select an event type (what is expected to happen).

   - Optionally, add a description.

#. Save and navigate to the Requirement details page (use the "Change" link in the admin).

   - Optionally, specify data rules in the "Data Rules" section:

#. Select a key path (specific data element).
#. Select an operator (how to compare the value).
#. Enter a value (expected parameter's value).

A badge template can have more than one requirement. For example, a badge
template issued on a specific course completion:

- Requirement 1:
    - event type: ``org.openedx.learning.course.passing.status.updated.v1``
    - description: ``On the Demo course completion.``
- Data rule 1:
    - key path: ``course.course_key``
    - operator: ``equals``
    - value: ``course-v1:edX+DemoX+Demo_Course``
- Data rule 2:
    - key path: ``is_passing``
    - operator: ``equals``
    - value: ``true``

5. Activate badge templates
---------------------------

#. In the Credentials admin panel, navigate to the badge template edit page.
#. Check the ``is active`` checkbox.

.. warning::

    Configuration updates for active badge templates are discouraged since they may cause inconsistent learner experience.
