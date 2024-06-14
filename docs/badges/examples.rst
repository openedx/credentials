Configuration examples
======================

These examples will show how to configure requirements and ``data rules`` for necessary use cases.

.. note::

    Any of the following examples can be combined for more specific use cases.


Implemented use cases
----------------------


1. ANY COURSE GRADE update
~~~~~~~~~~~~~~~~~~~~~~~~~~

    Not that useful. Any interaction (e.g. submit button click) with gradable block in any course leads to a badge.

1. **Requirement 1**:
    a. event type: ``org.openedx.learning.course.passing.status.updated.v1``
    b. description: ``On any grade update.``


2. ANY COURSE completion
~~~~~~~~~~~~~~~~~~~~~~~~

    Requires **passing grade** for any course. Once course'd grade becomes "passing" after gradable problem submission,
    a badge is awarded.

1. **Requirement 1**:
    a. event type: ``org.openedx.learning.course.passing.status.updated.v1``
    b. description: ``On any (not CCX) course completion.``
    c. **Data rule 1**:
        i. key path: ``is_passing``
        ii. operator: ``equals``
        iii. value: ``true``


3. ANY CCX course completion
~~~~~~~~~~~~~~~~~~~~~~~~~~~~

    Requires **passing grade** for any CCX course.

1. **Requirement 1**:
    a. event type: ``org.openedx.learning.ccx.course.passing.status.updated.v1``
    b. description: ``On any CCX course completion.``
    c. **Data rule 1**:
        i. key path: ``is_passing``
        ii. operator: ``equals``
        iii. value: ``true``


4. ANY COURSE completion EXCEPT a specific course
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

    Requires **passing grade** for any course **excluding** the "Demo" course.

1. **Requirement 1**:
    a. event type: ``org.openedx.learning.course.passing.status.updated.v1``
    b. description: ``On any course completion, but not the "Demo" course.``
    c. **Data rule 1**:
        i. key path: ``is_passing``
        ii. operator: ``equals``
        iii. value: ``true``
    d. **Data rule 2**:
        i. key path: ``course.course_key``
        ii. operator: ``not equals``
        iii. value: ``course-v1:edX+DemoX+Demo_Course``


5. SPECIFIC COURSE completion
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

    Requires **passing grade** for exact course ("Demo" course).

1. **Requirement 1**:
    a. event type: ``org.openedx.learning.course.passing.status.updated.v1``
    b. description: ``On the Demo course completion.``
    c. **Data rule 1**:
        i. key path: ``is_passing``
        ii. operator: ``equals``
        iii. value: ``true``
    d. **Data rule 2**:
        i. key path: ``course.course_key``
        ii. operator: ``equals``
        iii. value: ``course-v1:edX+DemoX+Demo_Course``


6. MULTIPLE SPECIFIC COURSES completion
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

    **All** specified courses must be completed.
    Different requirement groups force each requirement to be fulfilled.

1. **Requirement 1**:
    a. event type: ``org.openedx.learning.course.passing.status.updated.v1``
    b. description: ``On the "Demo" course completion.``
    c. group: ``A``
    d. **Data rule 1**:
        i. key path: ``is_passing``
        ii. operator: ``equals``
        iii. value: ``true``
    e. **Data rule 2**:
        i. key path: ``course.course_key``
        ii. operator: ``equals``
        iii. value: ``course-v1:edX+DemoX+Demo_Course``

2. **Requirement 2**:
    a. event type: ``org.openedx.learning.course.passing.status.updated.v1``
    b. description: ``On the "Other" course completion.``
    c. group: ``B``
    d. **Data rule 1**:
        i. key path: ``is_passing``
        ii. operator: ``equals``
        iii. value: ``true``
    e. **Data rule 2**:
        i. key path: ``course.course_key``
        ii. operator: ``equals``
        iii. value: ``course-v1:edX+DemoX+OTHER_Course``


7. SPECIFIC CCX course completion
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

    Requires **passing grade** for exact CCX course ("Demo CCX1" course).

1. **Requirement 1**:
    a. event type: ``org.openedx.learning.ccx.course.passing.status.updated.v1``
    b. description: ``On the Demo CCX1 course completion.``
    c. **Data rule 1**:
        i. key path: ``is_passing``
        ii. operator: ``equals``
        iii. value: ``true``
    d. **Data rule 2**:
        i. key path: ``course.ccx_course_key``
        ii. operator: ``equals``
        iii. value: ``ccx-v1:edX+DemoX+Demo_Course+ccx@1``

8. ANY CCX course completion ON a SPECIFIC MASTER course
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

    Requires **passing grade** for any "child" CCX course that based on the master "Demo" course.

1. **Requirement 1**:
    a. event type: ``org.openedx.learning.ccx.course.passing.status.updated.v1``
    b. description: ``On any Demo CCX course completion.``
    c. **Data rule 1**:
        i. key path: ``is_passing``
        ii. operator: ``equals``
        iii. value: ``true``
    d. **Data rule 2**:
        i. key path: ``course.master_course_key``
        ii. operator: ``equals``
        iii. value: ``course-v1:edX+DemoX+Demo_Course``

9. ANY CCX course completion ON a SPECIFIC MASTER course EXCEPT a SPECIFIC CCX course
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

    Complicated.
    Requires **passing grade** for **any "child" CCX course** that based on the master "Demo" course, **excluding** the "Demo CCX2" course.

1. **Requirement 1**:
    a. event type: ``org.openedx.learning.ccx.course.passing.status.updated.v1``
    b. description: ``On any Demo CCX course completion.``
    c. **Data rule 1**:
        i. key path: ``is_passing``
        ii. operator: ``equals``
        iii. value: ``true``
    d. **Data rule 2**:
        i. key path: ``course.master_course_key``
        ii. operator: ``equals``
        iii. value: ``course-v1:edX+DemoX+Demo_Course``
    e. **Data rule 3**:
        i. key path: ``course.ccx_course_key``
        ii. operator: ``not equals``
        iii. value: ``ccx-v1:edX+DemoX+Demo_Course+ccx@2``

10. ONE OF MULTIPLE SPECIFIC COURSES completion
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

    At least a single from the specified courses must be completed.
    Grouped requirements are processed as **"ANY FROM A GROUP"**.

1. **Requirement 1**:
    a. event type: ``org.openedx.learning.course.passing.status.updated.v1``
    b. description: ``On the "Demo" course completion.``
    c. group: ``A``
    d. **Data rule 1**:
        i. key path: ``is_passing``
        ii. operator: ``equals``
        iii. value: ``true``
    e. **Data rule 2**:
        i. key path: ``course.course_key``
        ii. operator: ``equals``
        iii. value: ``course-v1:edX+DemoX+Demo_Course``

2. **Requirement 2**:
    a. event type: ``org.openedx.learning.course.passing.status.updated.v1``
    b. description: ``On the "Other" course completion.``
    c. group: ``A``
    d. **Data rule 1**:
        i. key path: ``is_passing``
        ii. operator: ``equals``
        iii. value: ``true``
    e. **Data rule 2**:
        i. key path: ``course.course_key``
        ii. operator: ``equals``
        iii. value: ``course-v1:edX+DemoX+OTHER_Course``


11. SPECIFIC MASTER course OR ANY of its CCX courses EXCEPT a SPECIFIC CCX course completion
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

    Here requirements 1 and 2 are grouped, so any of them lead to a badge.

1. **Requirement 1**:
    a. event type: ``org.openedx.learning.course.passing.status.updated.v1``
    b. description: ``On the "Demo" course completion OR...``
    c. group: ``A``
    d. **Data rule 1**:
        i. key path: ``is_passing``
        ii. operator: ``equals``
        iii. value: ``true``
    e. **Data rule 2**:
        i. key path: ``course.course_key``
        ii. operator: ``equals``
        iii. value: ``course-v1:edX+DemoX+Demo_Course``

2. **Requirement 2**:
    a. event type: ``org.openedx.learning.ccx.course.passing.status.updated.v1``
    b. description: ``...OR any Demo CCX courses completion EXCLUDING CCX3.``
    c. group: ``A``
    d. **Data rule 1**:
        i. key path: ``is_passing``
        ii. operator: ``equals``
        iii. value: ``true``
    e. **Data rule 2**:
        i. key path: ``course.master_course_key``
        ii. operator: ``equals``
        iii. value: ``course-v1:edX+DemoX+Demo_Course``
    f. **Data rule 3**:
        i. key path: ``course.ccx_course_key``
        ii. operator: ``not equals``
        iii. value: ``ccx-v1:edX+DemoX+Demo_Course+ccx@3``

-----

Future work
-----------

1. Events set extension (e.g. "Email activation", "Profile data completion", "Course section completion", ...);
2. Repetitive events (e.g. "5 arbitrary courses completion");
3. Prerequisite events (e.g. "5 specific courses completion in a specified order");
4. Time-ranged event (e.g. "Arbitrary course completion during the February 2022");
5. Badge dependencies (e.g. "Badge A + Badge B = Badge C");
6. Multiple times same badge earning (e.g. "3 arbitrary course completions make badge earned x3");
