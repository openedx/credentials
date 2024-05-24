Quick Start
===========

    Learners *earn* badges based on Open edX platform activity.


0. Credly service prerequisites
-------------------------------

Since current Badges version is deeply integrated with the Credly service, Credly account is a prerequisite.

- a **Credly Organization** is expected to be created;
- 1 or more **badge templates** are expected to be created and activated in the Organization;
- Credly Organization **authorization token** is issued;

1. Enable feature
-----------------

Badges feature is optional and it is disabled by default.
So, it must be enabled to be accessible.

.. code-block::

    # LMS service:
    FEATURES["BADGES_ENABLED"] = True

    # Credentials service:
    BADGES_ENABLED = True

2. Configure Credly integration
-------------------------------

    Multiple Credly Organizations can be configured.

Enter the Credentials service admin interface and configure the integration with the Credly service:

- create a Credly Organization (`<credentials>/admin/badges/credlyorganization/`);
- set the UUID for the Organization;
- set the authorization token;

Check: the system pulls the Organization data and updates its name.


3. Synchronize badge templates
------------------------------

From the "Credly Organizations" list, select the Organization(s) you want to use and select ``Sync organization badge templates`` action.

The system pulls the list of badge templates from the Credly Organization. Navigate to the "Credly badge templates" list and check newly created templates.

4. Setup badge requirements
---------------------------

    Requirements describe **what** and **how** must happen on the system to earn a badge.

The crucial part of the badge template configuration is requirements specification.
At least one requirement must be associated with a badge template.

Enter the first badge template details page and configure its requirement(s):

- find "Badge Requirements" section;
- add new item and select an event type (what is expected to happen);
- optionally, put a description;
- save and navigate to the Requirement details (``Change`` link);

- optionally, specify a data rule(s) in the "Data Rules" section (how exactly it is expected to happen);
- add new item and describe the rule;
- select a key path - target payload parameter;
- select an operator - how to compare the value;
- enter a value - expected parameter's value;

.. note::

    A configuration for the badge template that must be issued on a **specific course completion** looks as following:

    - Requirement:
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

Once badge requirements are configured, it should be "enabled" to start "working".

Active badge templates start being taking into account immediately.

.. warning::

    Configuration updates for active badge template are discouraged since it may cause learners' inconsistent experience.

6. See users Badge Progress
---------------------------

Current badge progress can be seen in the "Badge progress records" section.

Since badge template can have more than one requirement, there can be partially completed badges.

7. See awarded user credentials
-------------------------------

Already earned badges are listed in the "Credly badges" list page.

    The Credly Badge is an extended version of a user credential record.

Once badge progress is complete (all requirements were *fulfilled*), the system:

- creates internal user credential (CredlyBadge);
- notifies about the badge awarding (public signal);
- requests Credly service to issue the badge (API request).

8. See issued Credly badges
---------------------------

Earned internal badges (user credentials) propagate to the Credly service.

On a successful Credly badge issuing the CredlyBadge user credential is updated with its requisites:

- external UUID;
- external state;

The Credly badge is visible in the Credly service.


9. Badge template withdrawal
----------------------------

Badge template can be deactivated by putting it in the inactive state (``is active`` checkbox).

Inactive badge templates are ignored during the processing.
