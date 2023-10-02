Endpoint for Learner Credential Status
######################################

Status
**Draft**

Context
*******

Because of the loose coupling between programs, courses and course-runs, there is a need for a mechanism to evaluate a learner's status in multiple courses in the context of a program.
The loose coupling means that a program is defined in Discovery by a list of courses. Those courses have course-runs, and the course-runs are automatically added to the program definition.
The program definition in Discovery can also have exceptions - course-runs that are excluded from the program.

The gap between courses included in a program vs actual course-runs completed by a learner can lead to situations where a learner believes that they have completed all the courses in a program. However, the program remains incomplete because the course-run they completed has been excluded from the program. The issue being that they don't have visibility into these exceptions.
These use cases are currently difficult to reconcile because the only way to correlate the courses that a learner has taken and the exception list for course-runs in a program is through the admin interface. For a system that only tracks what courses a learner has taken, additional queries need to be made to map the course-runs associated with the courses. 

There are teams that need to get the current status of a set of courses for a learner for issues such as subscriptions.
Support often has to determine the status of a learner's credentials with respect to a program to determine if a learner has completed a course on the exclude list.


Decision
********

Add an API to the Credentials service that takes a learner ID and a list of courses, and returns the completion status for the learner for each of the courses.

A follow up to the API will allow passing in a learner and a program, and the API will return the status for all the course-runs and tag any course-runs in the exclude list for that program.


Consequences
************

More load on credentials. 
Credentials may at times be out of sync with the system of record, platform. It is not the source of truth, so this endpoint will be helpful, but not definitive.

Rejected Alternatives
*********************

- Add the endpoint to platform.
  This was rejected because the long term plan is to move the course credential responsibilities to the Credentials IDA, and it would need to be
  reimplemented. It would be coming from the current source of truth, but platform may not have the discovery information needed for reconciling the program data.

References
**********

.. (Optional) List any additional references here that would be useful to the future reader. See `Documenting Architecture Decisions`_ for further input.

.. _Documenting Architecture Decisions: https://cognitect.com/blog/2011/11/15/documenting-architecture-decisions
