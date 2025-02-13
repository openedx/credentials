Quick Start
===========

.. note::

    This section includes brief information about the feature – what to start with; where to set up credentials, etc.

Currently Open edX supports two badge services: Credly and Accredible.

0. Prerequisites – service account
----------------------------------

To start using this feature a Credly or Accredible account is necessary.

For Credly:

1. Register on Credly and create your account.
2. Create Organization in Credly.
3. Create at least 1 badge template and activate it.


For Accredible:

1. Register on Accredible and create your account.
2. Create at least 1 group.

1. Enable feature
-----------------

Badges feature is optional and it is disabled by default. So, it must be enabled to be accessible.

.. code-block::

    # LMS service:
    FEATURES["BADGES_ENABLED"] = True

    # Credentials service:
    BADGES_ENABLED = True

2. Configure integration
-------------------------------

.. note::

    For detailed information, go to the `Configuration`_ section.

Go to the Credentials service admin panel and configure the integration with the service:

Credly
------

1. In the admin panel go to <credentials>/admin/badges/credly_organization to add Credly Organization.
    a. Add UUID (unique identifier) for the Credly organization
    b. Add the authorization token of the Credly organization.

Please note that UUID and authorization token will be given to you during the creation of the Credly Organization on the Credly side

Check: the system pulls the Organization's data and updates its name.

Accredible
-----------

1. Retrieve API Key from Accredible account settings. Go to the Accredible account settings -> Manage API Keys and create a new API Key.
2. In the admin panel go to ``<credentials>/admin/badges/accredibleapiconfig`` to add Accredible Group.
    a. Add API Key
    b. Add name for configuration

.. _Configuration: configuration.html


3. Synchronize badge templates
------------------------------
    Note: For detailed information, go to the `Configuration`_ section.

Credly
------

From the “Credly Organizations” list, select the Organization(s) you want to use and select ``Sync organization badge templates`` action.

The system pulls the list of badge templates from the Credly Organization. Navigate to the “Credly badge templates” list and check newly created templates.

Accredible
----------
From the Accredible API Configurations list, select the Configuration(s) you want to use and select ``Sync groups`` action.

The system pulls the list of groups from the Accredible account. Navigate to the “Accredible groups” list and check newly created groups.

.. _Configuration: configuration.html

4. Setup badge requirements
---------------------------

.. note::

    Requirements describe **what** and **how** must happen on the system to earn a badge.

The crucial part of the badge template configuration is the requirements specification. At least one requirement must be associated with a badge template.

Go to the first badge template details page (admin/badges/credly_badge_templates or admin/badges/accrediblegroup) and add requirements for it:

1. find the “Badge Requirements” section;
2. add a new item and select an event type (what is expected to happen);
    a. optionally, put a description;
3. save and navigate to the Requirement details (Change link);
    a. optionally, specify data rules in the “Data Rules” section (how exactly it is expected to happen);
4. add a new item and describe the rule;
5. select a key path - specific data element;
6. select an operator - how to compare the value;
7. enter a value - expected parameter’s value.

.. note::

    A configuration for the badge template that must be issued on a specific course completion looks as following:
    
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

It is possible to put more than one requirement in a badge template.

5. Activate configured badge templates
--------------------------------------

    To active a badge template check the ``is active`` checkbox on its edit page.

Once badge requirements are set up, it should be “enabled” to start “working”.

Once enabled, the badge template will be active and ready.

.. warning::

    Configuration updates for active badge templates are discouraged since they may cause learners’ inconsistent experience.

6. See users Badge Progress
---------------------------

Current badge progress can be seen in the “Badge progress records” section in the Credentials admin panel.

Since badge templates can have more than one requirement, there can be partially completed badges.

7. See awarded user credentials
-------------------------------

Already earned badges are listed in the "Credly badges" or "Accredible badges" section of the admin panel.

.. note::

    This badge is an extended version of a user credential record.

Once badge progress is complete (all requirements were *fulfilled*), the system:

1. creates internal user credentials (CredlyBadge or AccredibleBadge);
2. notifies about the badge awarding (public signal);
3. requests Credly or Accredible service to issue the badge (API request).

8. See issued badges
---------------------------

Earned internal badges (user credentials) spread to the badge service.

On a successful badge issuing, the CredlyBadge or AccredibleBadge user credential is updated with its requisites:

1. external UUID;
2. external state;

The Credly badge is visible in the Credly service.
The Accredible badge is visible in the Accredible service.


9. Badge template withdrawal
----------------------------

Badge template can be deactivated by putting it in the inactive state (``is active`` checkbox).

Inactive badge templates are ignored during the processing.
