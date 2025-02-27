Pathway Status
==============

Status
------
Accepted

Background
----------
Course discovery is now allowing pathways to be retired. The `course-discovery` API will continue to expose retired pathways, and it will rely on consumers to expose or process retired pathways as appropriate.

Decision
--------
The catalog app will now synchronize the `Pathway`'s `status` attribute.  In the absence of a populated `status`  attribute, a pathway will be considered  to have the status of `published`.
