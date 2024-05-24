Configuration
=============

The Badges feature is configured via the Credentials admin interface.

.. image:: ../_static/images/badges/badges-admin.png
        :alt: Badges administration

Credly Organizations
--------------------

    Multiple Credly Organizations can be configured.

**All communication between Open edX Credentials and Credly service happens on behalf of a Credly Organization.**

Enter "Credly Organizations" list page (`<credentials>/admin/badges/credlyorganization/`) and create a new item:

- to set the UUID use your Credly Organization identifier;
- to set the authorization token issue one in the Credly Organization's dashboard;

Check: the system pulls the Organization's details and updates its name.

In case of errors check used credentials for the Organization.

Badge templates
---------------

    **Badge template** is another **credential** type. Credly badge template is a kind of a badge template.

*Credly badge templates* (badge templates for brevity) are created in the Credly Organization's dashboard and then, if published, they are retrieved by the Credentials via API.

Synchronization
~~~~~~~~~~~~~~~

To synchronize Credly badge templates for the Organization one should:

- navigate "Credly badge templates" list page;
- select the Organization;
- use ``Sync organization badge templates`` action;

.. image:: ../_static/images/badges/badges-admin-credly-templates-sync.png
        :alt: Credly badge templates synchronization

On success, the system will update the list of Credly badge templates for the Organization:

- only badge templates with ``active`` state are pulled;
- Credly badge template records are created inactive (disabled);

.. image:: ../_static/images/badges/badges-admin-credly-templates-list.png
        :alt: Credly badge templates list

For the usage a badge template must be configured and activated first.

Badge Requirements
------------------

    Requirements describe **what** and **how** must happen on the system to earn a badge.

Badge Requirement(s) specification is a crucial part of badge template configuration.
At least one badge requirement must be associated with a badge template.

Badge Requirements are listed inline on a badge template detail page.

.. image:: ../_static/images/badges/badges-admin-template-requirements.png
        :alt: Credly badge template requirements

A badge template can can have multiple requirements. All badge requirements must be *fulfilled* to earn a badge.

Event type
~~~~~~~~~~

    Describes **what is expected to happen**.

Available event type subset is pre-configured in the application settings.

.. note::

    Technically, any public signal from the `openedx-events`_ library can be used for badge template requirements setup, if it includes user PII (UserData), so users can be identified.

Rules
~~~~~

A list of configured data rules (if any), see "Data Rules".

Description
~~~~~~~~~~~

**Description** is an optional human-readable reminder that describes what the requirement is about.

    Badge Requirement can be **deeper specified** via its Data Rules.

Group
~~~~~

Optional configuration (by default each badge requirement is assigned a separate Group).

Allows putting 2 or more badge requirements as a Group.
Requirements group is fulfilled if any of its requirements is fulfilled.

    "OR" logic is applied inside a Group.

.. image:: ../_static/images/badges/badges-admin-rules-group.png
        :alt: Badge requirement rules group

See `configuration examples`_.

Data Rules
----------

    Describes **how it is expected to happen**

Data Rules detail their parent Badge Requirement based on the expected event payload.

To edit/update a Data Rule:

- navigate to the Badge Requirement detail page (use ``Change`` inline link);
- find the "Data Rules" section and add a new item;

.. image:: ../_static/images/badges/badges-admin-requirement-rules.png
        :alt: Badge requirement rules edit

**Each data rule describes a single expected payload value:**

All key paths are generated based on the event type specified for the parent Badge Requirement.

.. image:: ../_static/images/badges/badges-admin-data-rules.png
        :alt: Badge requirement data rules

1. **Key path** - payload path to the target attribute
    - dot-separated string;
    - each event type has its unique pre-defined set of key paths;
2. **Operator** - comparison operation to apply between expected and actual values;
    - available operators: (payload)
        -  ``"="`` (equals);
        - ``"!="`` (not equals);
3. **Expected value** - an expected value for the target attribute
    - payload boolean positive values allowed: ``"true", "True", "yes", "Yes", "+"``;
    - payload boolean negative values allowed: ``"false", "False", "no", "No", "-"``;


Please, see `configuration examples`_ for clarity.

Badge Penalties
---------------

    Penalties allow badge progress resetting based on user activity.

Badge penalties are optional.
There could be 0 or more badge penalties configured for a badge template.

Each badge penalty is *targeted* to 1 or more badge requirements.
A penalty setup is similar to a badge requirement, but has different effect: it decreases badge progress for a user.

When a penalty has worked all linked badge requirements are "rolled back" (user's progress for such requirements is reset).

.. image:: ../_static/images/badges/badges-admin-penalty-rules.png
        :alt: Badge penalty rules edit

Activation
----------

Configured badge template can be activated:

- navigate to the badge template detail page;
- check ``Is active`` checkbox;

    Activated badge template starts "working" immediately.

.. image:: ../_static/images/badges/badges-admin-template-details.png
        :alt: Badge template data structure

Credly badge template record includes:

1. Core credential attributes;
2. Badge template credential attributes;
3. Credly service attributes (state, dashboard link);
4. Configured requirements;

.. _`configuration examples`: examples.html
.. _openedx-events: https://github.com/openedx/openedx-events