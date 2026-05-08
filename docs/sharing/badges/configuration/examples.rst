.. _Configuration examples for Badging:

Configuration Examples
======================

These examples show how to configure badge :ref:`requirements <badges-configuration-requirements>` and :ref:`data rules <badges-configuration-data-rules>` for common use cases.
Each example lists the fields as they appear on the requirement and data rule forms in the Credentials admin.

The following screenshots show the admin forms used in the examples below.

.. figure:: ../../../_static/images/badges/badges-admin-template-requirements.png
   :alt: Badge template detail page showing the inline list of badge requirements.

   Use this form to add or review requirement records for a badge template. For field descriptions and requirement behavior, see :ref:`badges-configuration-requirements`.

.. figure:: ../../../_static/images/badges/badges-admin-rules-group.png
   :alt: Badge requirement form showing the Group field.

   Use the Group field when a requirement should be evaluated together with other requirements by OR logic. For grouping rules and examples, see :ref:`badges-configuration-groups`.

.. figure:: ../../../_static/images/badges/badges-admin-data-rules.png
   :alt: Badge requirement form showing the Data Rules section.

   Use this form to configure event fields, group assignment, and data rules for a requirement. For data rule fields and matching behavior, see :ref:`badges-configuration-data-rules`.


Course Completion
-----------------

The examples below show common ways to configure badge requirements for course-completion and CCX-completion events.
Use them as starting points when you want to issue badges based on passing status, specific course keys, or combinations of course and CCX requirements.

ANY COURSE GRADE Update
~~~~~~~~~~~~~~~~~~~~~~~

    Triggers on any gradable interaction (e.g. submit button click) in any course. Rarely useful on its own.

- **Requirement 1**:
    a. event type: ``org.openedx.learning.course.passing.status.updated.v1``
    b. description: ``On any grade update.``


ANY COURSE Completion
~~~~~~~~~~~~~~~~~~~~~

    Requires **passing grade** for any course. Once a course grade becomes "passing" after a gradable problem submission,
    a badge is awarded.

- **Requirement 1**:
    a. event type: ``org.openedx.learning.course.passing.status.updated.v1``
    b. description: ``On any (not CCX) course completion.``
    c. **Data rule 1**:
        i. key path: ``is_passing``
        ii. operator: ``"=" (equals)``
        iii. value: ``true``


ANY COURSE Completion EXCEPT a Specific Course
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

    Requires **passing grade** for any course **excluding** the "Demo" course.

- **Requirement 1**:
    a. event type: ``org.openedx.learning.course.passing.status.updated.v1``
    b. description: ``On any course completion, but not the "Demo" course.``
    c. **Data rule 1**:
        i. key path: ``is_passing``
        ii. operator: ``"=" (equals)``
        iii. value: ``true``
    d. **Data rule 2**:
        i. key path: ``course.course_key``
        ii. operator: ``"!=" (not equals)``
        iii. value: ``course-v1:OpenedX+DemoX+Demo_Course``


SPECIFIC COURSE Completion
~~~~~~~~~~~~~~~~~~~~~~~~~~

    Requires **passing grade** for exact course ("Demo" course).

- **Requirement 1**:
    a. event type: ``org.openedx.learning.course.passing.status.updated.v1``
    b. description: ``On the Demo course completion.``
    c. **Data rule 1**:
        i. key path: ``is_passing``
        ii. operator: ``"=" (equals)``
        iii. value: ``true``
    d. **Data rule 2**:
        i. key path: ``course.course_key``
        ii. operator: ``"=" (equals)``
        iii. value: ``course-v1:OpenedX+DemoX+Demo_Course``

MULTIPLE SPECIFIC COURSES Completion
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

    **All** specified courses must be completed.
    Different requirement groups force each requirement to be fulfilled.

- **Requirement 1**:
    a. event type: ``org.openedx.learning.course.passing.status.updated.v1``
    b. description: ``On the "Demo" course completion.``
    c. group: ``A``
    d. **Data rule 1**:
        i. key path: ``is_passing``
        ii. operator: ``"=" (equals)``
        iii. value: ``true``
    e. **Data rule 2**:
        i. key path: ``course.course_key``
        ii. operator: ``"=" (equals)``
        iii. value: ``course-v1:OpenedX+DemoX+Demo_Course``

- **Requirement 2**:
    a. event type: ``org.openedx.learning.course.passing.status.updated.v1``
    b. description: ``On the "Other" course completion.``
    c. group: ``B``
    d. **Data rule 1**:
        i. key path: ``is_passing``
        ii. operator: ``"=" (equals)``
        iii. value: ``true``
    e. **Data rule 2**:
        i. key path: ``course.course_key``
        ii. operator: ``"=" (equals)``
        iii. value: ``course-v1:OpenedX+DemoX+OTHER_Course``


ONE OF MULTIPLE SPECIFIC COURSES Completion
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

    At least a single from the specified courses must be completed.
    Grouped requirements are processed as **"ANY FROM A GROUP"**.

- **Requirement 1**:
    a. event type: ``org.openedx.learning.course.passing.status.updated.v1``
    b. description: ``On the "Demo" course completion.``
    c. group: ``A``
    d. **Data rule 1**:
        i. key path: ``is_passing``
        ii. operator: ``"=" (equals)``
        iii. value: ``true``
    e. **Data rule 2**:
        i. key path: ``course.course_key``
        ii. operator: ``"=" (equals)``
        iii. value: ``course-v1:OpenedX+DemoX+Demo_Course``

- **Requirement 2**:
    a. event type: ``org.openedx.learning.course.passing.status.updated.v1``
    b. description: ``On the "Other" course completion.``
    c. group: ``A``
    d. **Data rule 1**:
        i. key path: ``is_passing``
        ii. operator: ``"=" (equals)``
        iii. value: ``true``
    e. **Data rule 2**:
        i. key path: ``course.course_key``
        ii. operator: ``"=" (equals)``
        iii. value: ``course-v1:OpenedX+DemoX+OTHER_Course``


CCX Course Completion
---------------------


ANY CCX Course Completion
~~~~~~~~~~~~~~~~~~~~~~~~~

    Requires **passing grade** for any CCX course.

- **Requirement 1**:
    a. event type: ``org.openedx.learning.ccx.course.passing.status.updated.v1``
    b. description: ``On any CCX course completion.``
    c. **Data rule 1**:
        i. key path: ``is_passing``
        ii. operator: ``"=" (equals)``
        iii. value: ``true``


SPECIFIC CCX Course Completion
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

    Requires **passing grade** for exact CCX course ("Demo CCX1" course).

- **Requirement 1**:
    a. event type: ``org.openedx.learning.ccx.course.passing.status.updated.v1``
    b. description: ``On the Demo CCX1 course completion.``
    c. **Data rule 1**:
        i. key path: ``is_passing``
        ii. operator: ``"=" (equals)``
        iii. value: ``true``
    d. **Data rule 2**:
        i. key path: ``course.ccx_course_key``
        ii. operator: ``"=" (equals)``
        iii. value: ``ccx-v1:OpenedX+DemoX+Demo_Course+ccx@1``

ANY CCX Course Completion on a Specific Master Course
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

    Requires **passing grade** for any "child" CCX course that based on the master "Demo" course.

- **Requirement 1**:
    a. event type: ``org.openedx.learning.ccx.course.passing.status.updated.v1``
    b. description: ``On any Demo CCX course completion.``
    c. **Data rule 1**:
        i. key path: ``is_passing``
        ii. operator: ``"=" (equals)``
        iii. value: ``true``
    d. **Data rule 2**:
        i. key path: ``course.master_course_key``
        ii. operator: ``"=" (equals)``
        iii. value: ``course-v1:OpenedX+DemoX+Demo_Course``

ANY CCX Course Completion on a Specific Master Course Except a Specific CCX Course
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

    Requires **passing grade** for **any "child" CCX course** that based on the master "Demo" course, **excluding** the "Demo CCX2" course.

- **Requirement 1**:
    a. event type: ``org.openedx.learning.ccx.course.passing.status.updated.v1``
    b. description: ``On any Demo CCX course completion.``
    c. **Data rule 1**:
        i. key path: ``is_passing``
        ii. operator: ``"=" (equals)``
        iii. value: ``true``
    d. **Data rule 2**:
        i. key path: ``course.master_course_key``
        ii. operator: ``"=" (equals)``
        iii. value: ``course-v1:OpenedX+DemoX+Demo_Course``
    e. **Data rule 3**:
        i. key path: ``course.ccx_course_key``
        ii. operator: ``"!=" (not equals)``
        iii. value: ``ccx-v1:OpenedX+DemoX+Demo_Course+ccx@2``


Specific Master Course OR Any of Its CCX Courses Except a Specific CCX Course
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

    Here requirements 1 and 2 are grouped, so any of them lead to a badge.

- **Requirement 1**:
    a. event type: ``org.openedx.learning.course.passing.status.updated.v1``
    b. description: ``On the "Demo" course completion OR...``
    c. group: ``A``
    d. **Data rule 1**:
        i. key path: ``is_passing``
        ii. operator: ``"=" (equals)``
        iii. value: ``true``
    e. **Data rule 2**:
        i. key path: ``course.course_key``
        ii. operator: ``"=" (equals)``
        iii. value: ``course-v1:OpenedX+DemoX+Demo_Course``

- **Requirement 2**:
    a. event type: ``org.openedx.learning.ccx.course.passing.status.updated.v1``
    b. description: ``...OR any Demo CCX courses completion EXCLUDING CCX3.``
    c. group: ``A``
    d. **Data rule 1**:
        i. key path: ``is_passing``
        ii. operator: ``"=" (equals)``
        iii. value: ``true``
    e. **Data rule 2**:
        i. key path: ``course.master_course_key``
        ii. operator: ``"=" (equals)``
        iii. value: ``course-v1:OpenedX+DemoX+Demo_Course``
    f. **Data rule 3**:
        i. key path: ``course.ccx_course_key``
        ii. operator: ``"!=" (not equals)``
        iii. value: ``ccx-v1:OpenedX+DemoX+Demo_Course+ccx@3``

-----

Potential Use Cases
-------------------

The following ideas are not yet implemented. If you have a use case for any of them, start a conversation on the `Open edX discussion forum`_.

- Events set extension (e.g. "Email activation", "Profile data completion", "Course section completion")
- Repetitive events (e.g. "5 arbitrary courses completion")
- Prerequisite events (e.g. "5 specific courses completion in a specified order")
- Time-ranged events (e.g. "Arbitrary course completion during February 2022")
- Badge dependencies (e.g. "Badge A + Badge B = Badge C")
- Multiple same badge earning (e.g. "3 arbitrary course completions make badge earned x3")

.. _Open edX discussion forum: https://discuss.openedx.org/
