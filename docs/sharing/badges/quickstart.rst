Badges Operator Quick Start
===========================

Currently Open edX supports two badge services: Credly and Accredible.

.. note::

   Both providers use the same concept - a **badge template** defines the badge design and awarding rules. Credly calls these "badge templates"; Accredible calls them "groups." This guide uses "badge template" as the generic term.

Prerequisites
-------------

To start using this feature a Credly or Accredible account is necessary.

For Credly:

1. Register on Credly and create your account.
2. Create Organization in Credly.
3. Create at least 1 badge template and activate it.


For Accredible:

1. Register on Accredible and create your account.
2. Create at least 1 group.

Enable feature
--------------

Badges feature is optional and disabled by default. It must be enabled to be accessible.

.. code-block:: python

    # LMS service:
    FEATURES["BADGES_ENABLED"] = True

    # Credentials service:
    BADGES_ENABLED = True

Configure integration
---------------------

.. note::

    For detailed information, go to the :ref:`badges-configuration` section.

Go to the Credentials service admin panel and configure the integration with the service:

Credly
~~~~~~

1. In the admin panel go to ``<credentials>/admin/badges/credlyorganization/`` to add Credly Organization.

   a. Add UUID (unique identifier) for the Credly organization
   b. Add the authorization token of the Credly organization.

UUID and authorization token are provided when you create the Credly Organization on the Credly side.

Check: the system pulls the Organization's data and updates its name.

Accredible
~~~~~~~~~~

1. Retrieve API Key from Accredible account settings. Go to the Accredible account settings -> Manage API Keys and create a new API Key.
2. In the admin panel go to ``<credentials>/admin/badges/accredibleapiconfig`` to add Accredible Group.

   a. Add API Key
   b. Add name for configuration


Synchronize badge templates
---------------------------

.. note::

    For detailed information, go to the :ref:`badges-configuration` section.

Credly
~~~~~~

From the "Credly Organizations" list, select the Organization(s) you want to use and select ``Sync organization badge templates`` action.

The system pulls the list of badge templates from the Credly Organization. Navigate to the "Credly badge templates" list and check newly created templates.

Accredible
~~~~~~~~~~

From the Accredible API Configurations list, select the Configuration(s) you want to use and select ``Sync groups`` action.

The system pulls the list of groups from the Accredible account. Navigate to the "Accredible groups" list and check newly created groups.

Setup badge requirements
------------------------

.. note::

    Requirements describe **what** and **how** must happen on the system to earn a badge.

The crucial part of the badge template configuration is the requirements specification. At least one requirement must be associated with a badge template.

Go to the first badge template details page (``admin/badges/credlybadgetemplate/`` or ``admin/badges/accrediblegroup/``) and add requirements for it:

1. find the "Badge Requirements" section;
2. add a new item and select an event type (what is expected to happen);

   a. optionally, put a description;

3. save and navigate to the Requirement details (Change link);

   a. optionally, specify data rules in the "Data Rules" section (how exactly it is expected to happen);

4. add a new item and describe the rule;
5. select a key path - specific data element;
6. select an operator - how to compare the value;
7. enter a value - expected parameter's value.

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

A badge template can have more than one requirement.

Activate configured badge templates
------------------------------------

To activate a badge template, check the ``is active`` checkbox on its edit page.

.. warning::

    Configuration updates for active badge templates are discouraged since they may cause inconsistent learner experience.
