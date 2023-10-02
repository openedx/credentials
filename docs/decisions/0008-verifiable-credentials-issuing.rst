Issue verifiable credentials to learners 
========================================

Status
------

Accepted


Context
-------

As of July 2023, the Credentials Service is used as backend to support programs certificates.
Administrators can configure certificates, and learners can view and share earned certificates with anyone
to prove their achievements on the Open edX platform.
However, the sharing options for earned credentials is very limited, also it's hard to verify printed credentials or
get any additional information beyond the data explicitly included on the earned certificate.

We want to adopt `verifiable credentials (VC)`_ to improve the sharing of the earned credentials, and enhance interoperability
with external digital credentials platforms and wallets.
This will allow learners to receive high-value credentials they can use in the real world.

Every verifiable credential is a set of one or more claims made by an issuer about a subject – learner in the Open edX context.
A verifiable credential is a tamper-evident credential that has authorship and can be cryptographically verified.
After issuing a verifiable credential, it can be used to build a verifiable presentation, which can also be cryptographically verified.

Verifiable credentials are closely related to decentralized digital identities and decentralized identifiers (DIDs).
DID is a portable URL-based identifier, associated with an entity, a thing with distinct and independent existence such as person,
organization, or device.
DIDs are used in a verifiable credential to associate it with a subject, so that a verifiable credential itself can be easily ported
from one repository to another without the need to reissue the credential.  
You can find more information on DIDs in the `W3C DID-core specification`_.

Except `Verifiable Credentials Data Model v1.1`_, there are other standards
that are based on the Verifiable Credentials, and therefore are fully compatible with it.
The most prominent are 1EdTech `Open Badges v3.0`_ and `The European Blockchain Services Infrastructure (EBSI) Verifiable Credentials`_.

The ecosystem of verifiable credentials is growing rapidly, and they are becoming more common in all types of education,
including the formal, informal, and non-formal education.  
The Digital Credentials Consortium (DCC), and The European Blockchain Services Infrastructure (EBSI)
are working towards making Verifiable Credentials accessible to anyone.

This ADR describes the implementation of the Verifiable Credentials issuing mechanism,
that will add the possibility to create and sign a verifiable credential, based on the user's achievements on the Open edX system. 



Decision
--------

To issue verifiable credentials, it is decided to create a new Django application in the Credentials Service named `verifiable_credentials`.
It will provide configuration options for verifiable credentials, interfaces, and utilities for verifiable credentials issuing.

The new application should be optional to run for the deployers of the Open edX system, it should be toggled using DjangoSetting toggle.

The application should provide extensibility options using plugins and other instruments, that will allow the Open edX deployers
and contributors to easily implement and enable new verifiable credentials backends.
These backends can be used to:

* build JSON-LD documents based on several VC based standards, e.g., `Verifiable Credentials Data Model v1.1`_,
  `Open Badges v3.0`_, `EBSI Verifiable Credentials`_;

* implement integrations with different verifiable credentials signing services, such as `SpruceID's didkit-python`_, `DCC's sign-and-verify`_, and other open-source and proprietary solutions.

* issue credentials directly to different mobile and web digital credentials wallets, such as `DCC's Learner Credentials Wallet (LCW)`_.

In addition to the new application, it was decided to implement three initial issuing and composition backends to:

* transform user credentials as programs certificates, that are stored in the Credentials Service to `JSON-LD`_ according to `Open Badges v3.0`_ specification;

* issue verifiable credentials directly to `DCC's Learner Credentials Wallet (LCW)`_;

* sign verifiable credentials with the library `didkit-python`_, the python bindings for the open-source Rust-based `DIDKit`_ library maintained by SpruceID.

We want to focus on the implementation of issuing the program certificates in the form of verifiable credentials,
and eventually support other credentials types that are available in the Credentials Service as well.

The issuer configuration would be set on the site or organization level. Administrator would have an option to enable verifiable credentials generation for some user credentials instances, and disable it for others.

Learners will see the list of all earned credentials that can be issued in a form of the verifiable credentials upon learners' request. 


Consequences
------------

Implementation of the verifiable credentials issuing mechanism in the Credentials Service will open new
ways for learners to share and prove their achievements outside the Open edX platform.


Rejected Alternatives
---------------------

* Using `Open Badges v2.0`_ as the main digital credentials standard for sharing digital credentials.

* Integration with `Europass Digital Credentials Infrastructure (EDCI)`_, the verifiable credentials standard based on XML documents.

* Using `JWT`_ instead of `JSON-LD`_ as `verifiable credentials assertion format`_.

* Integrate with the `DCC's sign-and-verify`_ REST API signing Node.JS server. 


References
----------

`Design for verifiable credentials integration into the Open edX`_

`Verifiable Credentials for Education, Employment, and Achievement Use Cases`_
 


.. _`verifiable credentials (VC)`: https://www.w3.org/TR/vc-data-model/
.. _`Verifiable Credentials Data Model v1.1`: https://www.w3.org/TR/vc-data-model/
.. _`W3C DID-core specification`: https://www.w3.org/TR/did-core/
.. _`Open Badges v3.0`: https://1edtech.github.io/openbadges-specification/ob_v3p0.html
.. _`The European Blockchain Services Infrastructure (EBSI) Verifiable Credentials`: https://ec.europa.eu/digital-building-blocks/wikis/display/EBSI/What+is+ebsi
.. _`EBSI Verifiable Credentials`: https://ec.europa.eu/digital-building-blocks/wikis/display/EBSI/What+is+ebsi
.. _`DCC's sign-and-verify`: https://github.com/digitalcredentials/sign-and-verify
.. _`DCC's Learner Credentials Wallet (LCW)`: https://lcw.app/
.. _`MATTR wallet`:  https://learn.mattr.global/docs/concepts/digital-wallets
.. _`JSON-LD`: https://www.w3.org/TR/vc-data-model/#json-ld
.. _`SpruceID's didkit-python`: https://github.com/spruceid/didkit-python
.. _`didkit-python`: https://github.com/spruceid/didkit-python
.. _`DIDKit`: https://github.com/spruceid/didkit
.. _`Open Badges v2.0`: https://www.imsglobal.org/sites/default/files/Badges/OBv2p0Final/index.html
.. _`Europass Digital Credentials Infrastructure (EDCI)`: https://github.com/european-commission-empl/European-Learning-Model
.. _`JWT`: https://www.rfc-editor.org/rfc/rfc7519
.. _`verifiable credentials assertion format`: https://w3c.github.io/vc-imp-guide/#benefits-of-json-ld-and-ld-proofs
.. _`Design for verifiable credentials integration into the Open edX`: https://openedx.atlassian.net/wiki/spaces/OEPM/pages/3490840577
.. _`Verifiable Credentials for Education, Employment, and Achievement Use Cases`: https://w3c-ccg.github.io/vc-ed-use-cases/
