Digital Badges
==============

A digital badge is a credential that embeds metadata (issuer, criteria,
evidence) following the `Open Badges`_ standard. Badges can represent
individual achievements such as completing a course or passing an exam.

Badge processing is driven by configured Open edX platform events
(such as course completion). The Badges feature issues badges through
external providers. Built-in support includes `Credly (by Pearson)`_
and `Accredible`_.

See :ref:`badges-settings` for the full list of supported events and
:ref:`badges-processing` for how events are handled.

Key concepts
------------

**Badge template**
   Defines a badge's design, name, and awarding rules. Called "group" in
   Accredible. For configuration details, see :ref:`badges-configuration`.

**Badge**
   The credential a learner earns when they fulfill all requirements of a
   badge template. For processing details, see :ref:`badges-processing`.

**Requirement**
   A condition tied to a specific event type (e.g. course completion) that
   must be met to earn a badge. For requirement fields and behavior, see :ref:`badges-configuration-requirements`.

**Data rule**
   A filter on a requirement's event payload that narrows when the
   requirement counts as fulfilled
   (e.g. ``course.course_key equals course-v1:OpenedX+DemoX+Demo_Course``).
   For configuration details, see :ref:`badges-configuration-data-rules`.

**Group**
   A way to organize requirements. Requirements in the same group use OR
   logic (any one fulfills the group). Requirements in different groups use
   AND logic (all groups must be fulfilled).
   For grouping behavior, see :ref:`badges-configuration-requirements`.

**Penalty**
   A rule that resets specific requirement progress when a triggering event
   occurs (e.g. grade drops below passing).
   For penalty setup, see :ref:`badges-configuration-penalties`.

----

To get started, follow the :ref:`badges-quickstart` guide.

.. toctree::
    :maxdepth: 1

    quickstart
    settings
    configuration/index
    processing
    management

.. _Open Badges: https://openbadges.org/
.. _Credly (by Pearson): https://info.credly.com/
.. _Accredible: https://www.accredible.com/
