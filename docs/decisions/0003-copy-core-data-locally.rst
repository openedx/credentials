Copy core data locally
======================

Status
------

Accepted

Context
-------

We want to be able to access data from external sources of truth and to
provide some guarantees about core functionality that is derived from
that data.

Open edX services generally try to be `Self-Contained
Systems <http://scs-architecture.org/>`__.

Decision
--------

For external data that is core to our functionality, we will store local
copies of that data. That way, we aren’t dependent on other services
being available.

Data that is not core to our functionality, we can query as needed from
other services.

Consequences
------------

We will need to provide end points or management commands, to allow us
to pull or be pushed the data, as appropriate.

For example, we keep a local copy of portions of the course catalog (for
which Discovery is the source of truth) and portions of the grades table
(for which LMS is the source of truth).
