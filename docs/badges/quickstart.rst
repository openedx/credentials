Quick Start
===========

.. note::
    
    This section includes brief information about the feature – what to start with; where to set up credentials, etc.

0. Prerequisites – Credly account
---------------------------------

To start using this feature a Credly account is necessary.

1. Register on Credly and create your account.
2. Create Organization in Credly.
3. Create at least 1 badge template and activate it.
4. Credly Organization 

1. Enable feature
-----------------

Badges feature is optional and it is disabled by default. So, it must be enabled to be accessible.

.. code-block::

    # LMS service:
    FEATURES["BADGES_ENABLED"] = True

    # Credentials service:
    BADGES_ENABLED = True

2. Configure Credly integration
-------------------------------

.. note::

    For detailed information, go to the `Configuration`_ section.

Go to the Credentials service admin panel and configure the integration with the Credly service:

1. In the admin panel go to <credentials>/admin/badges/credly_organization to add Credly Organization.
    a. Add UUID (unique identifier) for the Credly organization
    b. Add the authorization token of the Credly organization.

Please note that UUID and authorization token will be given to you during the creation of the Credly Organization on the Credly side

Check: the system pulls the Organization's data and updates its name.

.. _Configuration: configuration.html


3. Synchronize badge templates
------------------------------
    Note: For detailed information, go to the `Configuration`_ section.

From the “Credly Organizations” list, select the Organization(s) you want to use and select ``Sync organization badge templates`` action.

The system pulls the list of badge templates from the Credly Organization. Navigate to the “Credly badge templates” list and check newly created templates.

.. _Configuration: configuration.html

4. Setup badge requirements
---------------------------

.. note::

    Requirements describe **what** and **how** must happen on the system to earn a badge.

The crucial part of the badge template configuration is the requirements specification. At least one requirement must be associated with a badge template.

Go to the first badge template details page (admin/badges/credly_badge_templates) and add requirements for it:

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

Already earned badges are listed in the "Credly badges" section of the admin panel.

.. note::

    The Credly Badge is an extended version of a user credential record.

Once badge progress is complete (all requirements were *fulfilled*), the system:

1. creates internal user credentials (CredlyBadge);
2. notifies about the badge awarding (public signal);
3. requests Credly service to issue the badge (API request).

8. See issued Credly badges
---------------------------

Earned internal badges (user credentials) spread to the Credly service.

On a successful Credly badge issuing, the CredlyBadge user credential is updated with its requisites:

1. external UUID;
2. external state;

The Credly badge is visible in the Credly service.


9. Badge template withdrawal
----------------------------

Badge template can be deactivated by putting it in the inactive state (``is active`` checkbox).

Inactive badge templates are ignored during the processing.
