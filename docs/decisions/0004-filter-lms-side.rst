Filter some data on the LMS side
================================

Status
------

Accepted

Context
-------

The LMS is the source of truth for lots of data we are interested in.
Specifically, grade and course certificate data.

Course certificates are properly part of the Credentials service, but
for historical reasons, they are actually kept in the LMS. (Program
certificates are correctly part of Credentials.)

But we still care about them, to generate our student records. So the
LMS needs to tell us about them.

The grades table in the LMS is extremely large. To be notified of every
change there would be a load burden.

Additionally, it is operationally expensive to create a receiving worker
cluster for celery jobs on the Credentials side, unless there are
several other use cases, that it starts to make sense.

Open edX services generally try to be `Self-Contained
Systems <http://scs-architecture.org/>`__.

Decision
--------

Despite our desire to be self-contained, some Credentials business logic
needs to stay on the LMS side.

Until we have more use cases to receive celery jobs, we can’t write
celery tasks locally, to be called by the LMS for certain events.

Which means the LMS needs to run that logic.

And we don’t want the burden of sending all those grades events just to
be thrown on the floor on this side anyway, because they weren’t
relevant to a student record.

Consequences
------------

Changes to the criteria for which course run certificates and grades are
interesting to a student record need to be made in two places: the LMS
and Credentials, depending on where the specific logic is kept.

We’ll need to keep endpoints around to receive data from the LMS
(currently we need a certificate and grades API).
