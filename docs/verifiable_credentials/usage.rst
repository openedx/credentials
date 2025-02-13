Usage
=====

The Open edX platform allows students to earn credentials (e.g. course certificates, program certificates). Based on such credentials learners are able to create a digital cryptographically proven piece of data - a verifiable credential.

.. note::
    Verifiable credentials are intended for machines.

A single Open edX achievement can be used as a source for numerous verifiable credentials (identical or different data models).

Verifiable credential includes data about:

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
    - there is always at least one issuer - organization/university/etc. who "confirms" credential's data is the Truth;
- how to check if it is still valid (status)
    - there are different status check methods;
    - there are different reasons for status update (source achievement revocation, for example);

**All that data is signed, so it can't be tampered in any way - that's the point.**

Learners
--------

The general usage flow is the following:

- **Student** finishes a course/program and **earns an achievement/credential** (e.g. Program Certificate X);
- **Student requests a verifiable credential** that confirms Program Certificate X exists (additional background can be included as well - e.g. average/total grade, etc.);
- The **Open edX platform creates (issues)** a verifiable credential on behalf of related Issuer (Organization/University/School);
- **Verifiable credential is uploaded** to some Learner's storage (verifiable credentials wallet, a mobile/web app);
- **Student presents** a verifiable credential to any Interested Party (another Org/University/School);
- **Interested Party verifies** a verifiable credential's status - checks if it wasn't tampered in any way; checks if it still has valid status (not expired, not revoked);

.. note::
    Please, see the `Learner Record micro-frontend`_ for details.

Administrators
--------------

The Open edX users with administrator rights are able to manage/monitor the Verifiable Credentials application within the Credentials IDA admin site.

.. note::
    Please, see the `Verifiable Credentials application`_ for details.

Relying Parties
---------------

Third-parties whom a verifiable credential is presented want to ensure the current status of such artifact. That's where the `Status List`_ mechanism comes into play.


.. _Learner Record micro-frontend: components.html#learner-record-microfrontend
.. _Verifiable Credentials application: components.html#verifiable-credentials-application
.. _Status List: components.html#status-list-api