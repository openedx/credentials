Credentials POST as update-or-create
====================================

Status
------

Accepted

Context
-------

The LMS wants to notify the Credential service whenever a user
credential is created or changed (status changes, different attributes,
etc).

But the LMS doesn't know what the resource ID is for a given credential
(doesn't know what the uuid is) in order to do a traditional PUT for
that resource. It could find it out if it did a round-trip first. But
that's a pain and inefficient.

Instead, we want a way to just tell Credentials, "here is a bundle of
data, just make it true."

Decision
--------

Despite it being slightly non-RESTful, we'll treat a POST on the
credentials or grades endpoints as an update-or-create instead of the
normal just-create.
