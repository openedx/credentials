Issue verifiable credentials to learners in the Learner Record MFE
==================================================================

Status
------

Accepted


Context
-------

Following the `decision <https://github.com/openedx/credentials/issues/1735>`_ to integrate `verifiable credentials`_ into the Credentials Service,
this ADR describes the implementation of the user interface, so that learners can request verifiable credentials based on their achievements in the Open edX system.

To generate a verifiable credential, the learner needs to provide their wallet DID.
In most digital credentials wallets, it can be done automatically from the mobile application by either scanning a QR code or opening a deep link.
The QR code or the deep link include additional parameters, which allow the mobile app to prepare a request to the server and receive signed, verifiable credentials.

Learners can issue the same Open edX credentials multiple times, but every time a verifiable credential is issued,
it will have a unique proof. Therefore, every issued verifiable credential is unique.

Decision
--------

* It is decided to implement the user interface for issuing credentials in the `Learner Record`_ micro-frontend, as it currently contains views for a learners current status in a program and the ability to share any earned credentials publicly or with institutions.

* Since the verifiable credentials functionality is optional for Open edX deployers, it has been decided to introduce a flag toggle in the `Learner Record`_ MFE, called 'ENABLE_VERIFIABLE_CREDENTIALS'. If this flag is disabled, the functionality related to verifiable credentials will not be available for users.

* The MFE should determine the user's device type, whether it is a desktop or mobile device. If the user opens verifiable credentials interface from desktop, the QR Code generated on a server should be displayed. If the user requests its credentials from a mobile device, the option to download the credentials using a deep link is shown.

* The learner may choose several credentials to issue, and then add them one-by-one into the digital wallet app.

Consequences
------------

Learners will have greater opportunities to share the Open edX credentials in the real world.

The `Learner Record`_ micro-frontend will be extended with an optional functionality for verifiable credentials.

Rejected Alternatives
---------------------

* Create a new micro-frontend for verifiable credentials.
 
* Use Django templates and legacy theming to implement user interface for the verifiable credentials in the Credentials Service. 

References
----------

Technical design proposal for verifiable credentials: https://openedx.atlassian.net/wiki/spaces/OEPM/pages/3490840577/Verifiable+Credentials+design#Design-Proposal

User Interface wireframes: https://openedx.atlassian.net/wiki/spaces/OEPM/pages/3490840577/Verifiable+Credentials+design#MFE-wireframes

.. _`verifiable credentials`: https://www.w3.org/TR/vc-data-model/

.. _`Learner Record`:  https://github.com/openedx/frontend-app-learner-record
