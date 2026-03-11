Digital Badges
==============

    The Badges feature allows learners to earn achievements (badges) for their learning activities.

- A **badge template** (called "group" in Accredible) defines a badge's design, name, and awarding rules.
- A **badge** is the credential a learner earns when they fulfill all requirements of a badge template.

The Badges feature integrates with `Credly (by Pearson)`_ and `Accredible`_ services, but can also be used independently.

What is Credly?
---------------

**Credly** is an end-to-end solution for creating, issuing, and managing digital Credentials. Organizations use **Credly** to recognize their learners' achievements.
Learners can store badges in their Credly profile to visualize their professional success - which courses were completed and when.

Badges provide employers and peers concrete evidence of what learners have accomplished to earn their credential and what they are capable of.

Badges are typically finer-grained than a traditional course certificate. They are meant to introduce game mechanics to have more frequent sources of motivation than one would get from a cumulative certificate.

What is Accredible?
--------------------

**Accredible** allows for the design and issuance of verifiable digital badges and certificates that showcase acquired skills, earning criteria, and evidence of learning. Learn more about Accredible on the `Accredible features page`_.


Glossary
--------

1. **Badge template** - a template for a badge (with design, name, and description) used to set up rules for awarding badges to learners. Called "group" in Accredible.

2. **Requirement** - a condition that must be met to earn a badge, tied to a specific event type (e.g. course completion).

3. **Data rule** - a filter on a requirement's event payload (e.g. ``course.course_key equals course-v1:edX+DemoX``).

4. **Group** - requirements in the same group use OR logic (any one fulfills the group). Requirements in different groups use AND logic.

5. **Penalty** - a rule that resets badge progress when a learner no longer meets a requirement (e.g. grade drops below passing).

----

.. toctree::
    :maxdepth: 2

    quickstart
    settings
    configuration/index
    processing
    management

.. _Credly (by Pearson): https://info.credly.com/
.. _Accredible: https://www.accredible.com/
.. _Accredible features page: https://www.accredible.com/features
