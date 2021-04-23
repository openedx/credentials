Certificate Available Date
==========================

Status
------
Accepted

Background
----------
The ``Certificate Available`` date from edx-platform is stored on the ``UserCredential`` for each user as they are earned
in an attribute called ``visible_date``. This value is sent from the edx-platform in the following situations:

* A course team updates the ``Certificate Available`` date in the course run settings and an update is sent for all
  certificates earned in that course run.
* A learner completes a course and is awarded a course certificate in the edx-platform. The date sent in this case will be
  ``Certificate Available`` date if the course is instructor paced, the ``Certificate Available`` date is set, and
  ``AUTO_CERTIFICATE_GENERATION`` is enabled. Otherwise it is the ``modified`` date of the course certificate.

The ``visible_date`` would also be calculated for program ``UserCredentials`` in the edx-platform and sent
to Credentials when a user is awarded a program ``UserCredential``.

The issues with this approach are:

* It is prone to synchronization issues.
* The ``Certificate Available`` date is always set at the course run level and the platform does not support setting this date per user.
* The program ``UserCredentials`` is never updated when the course run ``Certificate Available`` dates are changed.
* The ``Certificate Available`` date is used only for instructor paced course runs in edx-platform. As a result
  the ``visible_date`` will at times equal the date that the course certificate was last modified. This dual usage of the
  ``visible_date`` attribute on the ``UserCredential`` causes confusion for users.

Decision
--------
To better support the design and current implementation we are moving the ``Certificate Available`` date to the
``CourseCertificate`` model for the course run in Credentials.

This date will be set or updated in the following scenarios:

#. When the ``CourseCertificate`` entry is created for a course run. This occurs the first time a UserCredential for
   a course run is received.
#. When the ``Certificate Available`` date is changed in Studio by the course team an update should be sent from edx-platform
   to Credentials via web API.

The new ``Certificate Available`` date in the ``CourseCertificate`` model should store the  ``Certificate Available`` date
is there is one and be ``None`` otherwise.
