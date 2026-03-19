.. _vc-usage:

Usage
=====

The Open edX platform allows students to earn credentials (e.g. course
certificates, program certificates). Based on these credentials, learners can
create a digitally signed, cryptographically provable artifact - a verifiable
credential.

.. note::
    Verifiable credentials are machine-verifiable, meaning they can be
    automatically validated by software without human intervention.

A single Open edX achievement can be used as a source for multiple verifiable
credentials (identical or different data models).

A verifiable credential includes data about:

- who has achieved it (subject)
    - student's unique decentralized identifier (DID);
    - student's arbitrary personal data (optional);
- what exactly was achieved (credential)
    - type (program or course certificate);
    - title (program or course name, possibly courses list);
- when it happened (timestamp)
    - date and time verifiable credential was created (issued);
    - expiration moment (optionally);
- who proves it (issuer)
    - there is always at least one issuer - organization/university/etc. who
      confirms the credential's data is authentic;
- how to check if it is still valid (status)
    - there are different status check methods;
    - there are different reasons for status update (source achievement
      revocation, for example).

**All of this data is cryptographically signed, making it tamper-proof.**

Learners
--------

The general usage flow is the following:

- **Student** finishes a course or program and **earns a credential** (e.g.
  Course Certificate Y or Program Certificate X).
- **Student requests a verifiable credential** that confirms the certificate
  exists (additional context can be included as well - e.g. average/total
  grade, etc.).
- The **Open edX platform creates (issues)** a verifiable credential on
  behalf of the related Issuer (Organization/University/School).
- **Verifiable credential is uploaded** to the learner's storage (a
  verifiable credentials wallet - mobile or web app).
- **Student presents** the verifiable credential to any relying party
  (another Org/University/School).
- **Relying party verifies** the verifiable credential's status - checks
  that it has not been tampered with, and that it still has a valid status
  (not expired, not revoked).

.. note::
    See the :ref:`Learner Record micro-frontend <vc-learner-record-mfe>` for details.

Administrators
--------------

Open edX users with administrator rights can manage and monitor the Verifiable
Credentials application within the Credentials IDA admin site.

.. note::
    See the :ref:`Verifiable Credentials application <vc-application>` for details.

Relying Parties
---------------

Third parties to whom a verifiable credential is presented need to confirm its
current status. The :ref:`Status List <vc-status-list-api>` mechanism enables
this verification.


