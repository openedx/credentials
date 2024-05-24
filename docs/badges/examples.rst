Configuration examples
======================

These examples will put some light on how to configure requirements and data rules for desired use cases.

.. note::

    **Any of the following examples can be combined together for more specific use cases**.


Implemented use cases
----------------------


1. ANY COURSE GRADE update
~~~~~~~~~~~~~~~~~~~~~~~~~~

    Not that useful. Any interaction (e.g. submit button click) with gradable block in any course leads to a badge.

- Requirement 1:
    - event type: ``org.openedx.learning.course.passing.status.updated.v1``
    - description: ``On any grade update.``


2. ANY COURSE completion
~~~~~~~~~~~~~~~~~~~~~~~~

    Requires **passing grade** for any course. Once course'd grade becomes "passing" after gradable problem submission,
    a badge is awarded.

- Requirement 1:
    - event type: ``org.openedx.learning.course.passing.status.updated.v1``
    - description: ``On any (not CCX) course completion.``
    - Data rule 1:
        - key path: ``is_passing``
        - operator: ``equals``
        - value: ``true``


3. ANY CCX course completion
~~~~~~~~~~~~~~~~~~~~~~~~~~~~

    Requires **passing grade** for any CCX course.

- Requirement 1:
    - event type: ``org.openedx.learning.ccx.course.passing.status.updated.v1``
    - description: ``On any CCX course completion.``
    - Data rule 1:
        - key path: ``is_passing``
        - operator: ``equals``
        - value: ``true``


4. ANY COURSE completion EXCEPT a specific course
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

    Requires **passing grade** for any course **excluding** the "Demo" course.

- Requirement 1:
    - event type: ``org.openedx.learning.course.passing.status.updated.v1``
    - description: ``On any course completion, but not the "Demo" course.``
    - Data rule 1:
        - key path: ``is_passing``
        - operator: ``equals``
        - value: ``true``
    - Data rule 2:
        - key path: ``course.course_key``
        - operator: ``not equals``
        - value: ``course-v1:edX+DemoX+Demo_Course``


5. SPECIFIC COURSE completion
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

    Requires **passing grade** for exact course ("Demo" course).

- Requirement 1:
    - event type: ``org.openedx.learning.course.passing.status.updated.v1``
    - description: ``On the Demo course completion.``
    - Data rule 1:
        - key path: ``is_passing``
        - operator: ``equals``
        - value: ``true``
    - Data rule 2:
        - key path: ``course.course_key``
        - operator: ``equals``
        - value: ``course-v1:edX+DemoX+Demo_Course``


6. MULTIPLE SPECIFIC COURSES completion
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

    **All** specified courses must be completed.
    Different requirement groups force each requirement to be fulfilled.

- Requirement 1:
    - event type: ``org.openedx.learning.course.passing.status.updated.v1``
    - description: ``On the "Demo" course completion.``
    - group: ``A``
    - Data rule 1:
        - key path: ``is_passing``
        - operator: ``equals``
        - value: ``true``
    - Data rule 2:
        - key path: ``course.course_key``
        - operator: ``equals``
        - value: ``course-v1:edX+DemoX+Demo_Course``

- Requirement 2:
    - event type: ``org.openedx.learning.course.passing.status.updated.v1``
    - description: ``On the "Other" course completion.``
    - group: ``B``
    - Data rule 1:
        - key path: ``is_passing``
        - operator: ``equals``
        - value: ``true``
    - Data rule 2:
        - key path: ``course.course_key``
        - operator: ``equals``
        - value: ``course-v1:edX+DemoX+OTHER_Course``


7. SPECIFIC CCX course completion
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

    Requires **passing grade** for exact CCX course ("Demo CCX1" course).

- Requirement 1:
    - event type: ``org.openedx.learning.ccx.course.passing.status.updated.v1``
    - description: ``On the Demo CCX1 course completion.``
    - Data rule 1:
        - key path: ``is_passing``
        - operator: ``equals``
        - value: ``true``
    - Data rule 2:
        - key path: ``course.ccx_course_key``
        - operator: ``equals``
        - value: ``ccx-v1:edX+DemoX+Demo_Course+ccx@1``

8. ANY CCX course completion ON a SPECIFIC MASTER course
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

    Requires **passing grade** for any "child" CCX course that based on the master "Demo" course.

- Requirement 1:
    - event type: ``org.openedx.learning.ccx.course.passing.status.updated.v1``
    - description: ``On any Demo CCX course completion.``
    - Data rule 1:
        - key path: ``is_passing``
        - operator: ``equals``
        - value: ``true``
    - Data rule 2:
        - key path: ``course.master_course_key``
        - operator: ``equals``
        - value: ``course-v1:edX+DemoX+Demo_Course``

9. ANY CCX course completion ON a SPECIFIC MASTER course EXCEPT a SPECIFIC CCX course
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

    Complicated.
    Requires **passing grade** for **any "child"** CCX course that based on the master "Demo" course, **excluding** the "Demo CCX2" course.

- Requirement 1:
    - event type: ``org.openedx.learning.ccx.course.passing.status.updated.v1``
    - description: ``On any Demo CCX course completion.``
    - Data rule 1:
        - key path: ``is_passing``
        - operator: ``equals``
        - value: ``true``
    - Data rule 2:
        - key path: ``course.master_course_key``
        - operator: ``equals``
        - value: ``course-v1:edX+DemoX+Demo_Course``
    - Data rule 3:
        - key path: ``course.ccx_course_key``
        - operator: ``not equals``
        - value: ``ccx-v1:edX+DemoX+Demo_Course+ccx@2``

10. ONE OF MULTIPLE SPECIFIC COURSES completion
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

    At least a single from the specified courses must be completed.
    Grouped requirements are processed as **"ANY FROM A GROUP"**.

- Requirement 1:
    - event type: ``org.openedx.learning.course.passing.status.updated.v1``
    - description: ``On the "Demo" course completion.``
    - group: ``A``
    - Data rule 1:
        - key path: ``is_passing``
        - operator: ``equals``
        - value: ``true``
    - Data rule 2:
        - key path: ``course.course_key``
        - operator: ``equals``
        - value: ``course-v1:edX+DemoX+Demo_Course``

- Requirement 2:
    - event type: ``org.openedx.learning.course.passing.status.updated.v1``
    - description: ``On the "Other" course completion.``
    - group: ``A``
    - Data rule 1:
        - key path: ``is_passing``
        - operator: ``equals``
        - value: ``true``
    - Data rule 2:
        - key path: ``course.course_key``
        - operator: ``equals``
        - value: ``course-v1:edX+DemoX+OTHER_Course``


11. SPECIFIC MASTER course OR ANY of its CCX courses EXCEPT a SPECIFIC CCX course completion
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

    Here requirements 1 and 2 are grouped, so any of them lead to a badge.

- Requirement 1:
    - event type: ``org.openedx.learning.course.passing.status.updated.v1``
    - description: ``On the "Demo" course completion OR...``
    - group: ``A``
    - Data rule 1:
        - key path: ``is_passing``
        - operator: ``equals``
        - value: ``true``
    - Data rule 2:
        - key path: ``course.course_key``
        - operator: ``equals``
        - value: ``course-v1:edX+DemoX+Demo_Course``

- Requirement 2:
    - event type: ``org.openedx.learning.ccx.course.passing.status.updated.v1``
    - description: ``...OR any Demo CCX courses completion EXCLUDING CCX3.``
    - group: ``A``
    - Data rule 1:
        - key path: ``is_passing``
        - operator: ``equals``
        - value: ``true``
    - Data rule 2:
        - key path: ``course.master_course_key``
        - operator: ``equals``
        - value: ``course-v1:edX+DemoX+Demo_Course``
    - Data rule 3:
        - key path: ``course.ccx_course_key``
        - operator: ``not equals``
        - value: ``ccx-v1:edX+DemoX+Demo_Course+ccx@3``

-----

Future work
-----------

- Events set extension (e.g. "Email activation", "Profile data completion", "Course section completion", ...);
- Repetitive events (e.g. "5 arbitrary courses completion");
- Prerequisite events (e.g. "5 specific courses completion in a specified order");
- Time-ranged event (e.g. "Arbitrary course completion during the February 2022");
- Badge dependencies (e.g. "Badge A + Badge B = Badge C");
- Multiple times same badge earning (e.g. "3 arbitrary course completions make badge earned x3");
