0005 Program ID in UserCreditPathway
####################################

Status
******

Accepted


Context
*******

The ``Pathway`` model represents a way for learners to request credit for a ``Program`` from an institution. A ``Pathway`` can be associated with many ``Program``\ s, and any ``Program`` may be associated with many ``Pathway``\ s.

This is specific to ``Program``, and not applied to ``Curriculum`` which is a separate implementation of programs, but mostly used for Masters Degrees.

The ``UserCreditPathway`` model represents a record of any time a learner has requested credit using a ``Pathway``. This keeps track of only the ``User`` ID, the ``Pathway`` ID, and a ``status`` column (which indicates whether or not the email requesting credit has actually been sent).

We create a ``UserCreditPathway`` record whenever a learner requests credit for a ``Program`` on their Program Record page. Once a ``UserCreditPathway`` record has been created associating that ``User`` with that ``Pathway``, we do not allow the same ``User`` to request credit along the same ``Pathway`` again. (Presumably, this was to prevent users from spamming institutions with emails requesting credit.)

Note that the ``UserCreditPathway`` model does not keep track of the ``Program`` for which credit was requested, only the ``Pathway``. Since a ``Pathway`` can be associated with multiple ``Program``, we don’t have a record of which ``Program`` the user was requesting credit for.

This is causing some problems:

Reporting
=========

There may be a business case for understanding which ``Program``\ s users most often want to request credit for. This is not possible to understand with the current data.

Credit for Multiple Programs
============================

Because we prevent users from requesting credit along the same ``Pathway`` more than once, and because multiple ``Program``\ s may be associated with the same ``Pathway``, users who complete multiple ``Program``\ s that use the same ``Pathway`` can only request credit for one ``Program``.

Requesting Credit Before Completion
===================================

Users are allowed to request credit for a given ``Program`` before they have completed the ``Program``. (There are some imaginable business reasons for allowing this.) However, due to our current constraints, they are not able to request credit again once they do complete the ``Program``.

We have some existing code that tries to mitigate this by resending a request for credit when a learner is awarded a program certificate: if that learner already has a ``UserCreditPathway`` record along the relevant pathway, we automatically send the credit request again. The learner does not consent to it, and they are not notified that the request has been resent.

Decision
********

We will add the ``program_id`` to the ``UserCreditPathway`` model. This will be added at the same point that the ``UserCreditPathway`` record is first created: when the user through the UI decides to request credit from an institution. We already have the ``program_id`` at this point, but we have not been saving it.

Note: this ``program_id`` is the ID of the relevant ``Program`` in the Credentials service. This ID differs from the program ID in Discovery or the LMS. The ``program_uuid`` can be found by joining to the related ``Program`` object.

We will remove any checks preventing learners from re-requesting credit. We will no longer check for existing ``UserCreditPathway`` records when determining what options to show in the UI.

We will remove the code that resubmits credit requests upon program completion.

Consequences
************

There will now be data available showing which ``Program``\ s learners have requested credit for, along with the ``Pathway``\ s used. This can be used for reporting and business purposes as necessary.

However, this data will only start being collected at the time this feature is released. Any preexisting records in the ``UserCreditPathway`` table will not include the ``program_id``; that field will be ``null``.

Learners will now be able to request credit for multiple ``Program``\ s, even if they use the same ``Pathway``.

Learners will now be able to re-request credit for the same ``Program``. This prevents students from getting stuck if they requested credit before completion, and also opens up the risk of learners spamming institutions with credit requests.

No automatic process will request credit on the learner’s behalf.

There will be some changes in the UI to accommodate this shift.

Note: with this decision, the ``UserCreditPathway`` model will now only keep a record of these credit requests; it will no longer be used for any application logic.

Rejected Alternatives
*********************

ProgramCertRecord ID
====================

Instead of adding the Credentials ``Program`` ID to the ``UserCreditPathway`` model, we considered adding the ``ProgramCertRecord`` ID. A ``ProgramCertRecord`` is created whenever a learner decides to share their progress in a program (either publicly or by requesting credit). The ``ProgramCertRecord`` model links a ``Program`` and a ``User`` with a ``uuid``. That ``uuid`` is used to generate a public link to the learner’s Program Record page. This link is what is sent to institutions when credit is requested, or can be shared by the learner however they wish.

Using the ``ProgramCertRecord`` ID could make sense, since the URL that it represents is technically what the learner is sharing with the institution.

However, we are mostly interested in adding a field to help us understand which ``Program`` was shared, so we are choosing to link the ``Program`` directly instead. Also, the ``ProgramCertRecord`` model is confusing: from the name, it would be easy to think that a ``ProgramCertRecord`` connects a ``User``, a ``Program``, and a program certificate; or that a ``ProgramCertRecord`` exists for every learner who has completed a course in a program, or else for learners who have completed every course in a program. It does none of these things. It no longer has anything to do with certificates, and a ``ProgramCertRecord`` only exists when a learner has decided to share their progress in a program. We would like to move away from this confusing model.

References
**********

Pathways Documentation: https://edx-credentials.readthedocs.io/en/latest/pathways.html
