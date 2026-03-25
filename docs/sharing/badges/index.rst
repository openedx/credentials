Digital Badges
==============

A digital badge is a credential that embeds metadata (issuer, criteria,
evidence) following the `Open Badges`_ standard. Badges can represent
individual achievements such as completing a course or passing an exam.

The Badges feature issues badges through external providers. Built-in
support includes `Credly (by Pearson)`_ and `Accredible`_, with the
ability to add custom providers.

Key concepts
------------

**Badge template**
   Defines a badge's design, name, and awarding rules. Called "group" in
   Accredible.

**Badge**
   The credential a learner earns when they fulfill all requirements of a
   badge template.

**Requirement**
   A condition that must be met to earn a badge, tied to a specific event
   type (e.g. course completion).

**Data rule**
   A filter on a requirement's event payload
   (e.g. ``course.course_key equals course-v1:edX+DemoX``).

**Group**
   Requirements in the same group use OR logic (any one fulfills the group).
   Requirements in different groups use AND logic.

**Penalty**
   A rule that resets badge progress when a learner no longer meets a
   requirement (e.g. grade drops below passing).

----

.. toctree::
    :maxdepth: 2

    quickstart
    settings
    configuration/index
    processing
    management

.. _Open Badges: https://openbadges.org/
.. _Credly (by Pearson): https://info.credly.com/
.. _Accredible: https://www.accredible.com/
