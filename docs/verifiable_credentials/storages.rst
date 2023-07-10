Storages
========

Currently there is the only digital wallet is supported for production.

Learner Credential Wallet
-------------------------

`Official web-site`_:

    Learner Credential Wallet is an open source mobile wallet developed by the Digital Credentials Consortium, a network of leading international universities designing an open infrastructure for academic credentials.

Learner Credential Wallet (LCWallet) is a mobile app available for Android and IOS devices.

Usage prerequisites
~~~~~~~~~~~~~~~~~~~

LCWallet maintainer (`Digital Credentials Consortium`_) requires verifiable credentials issuer to be whitelisted (included to the trusted issuers list - `community issuer registry`_).

.. note::

    For development/testing purposes a `Sandbox Registry`_ is available.

Learner experience
~~~~~~~~~~~~~~~~~~

This explains a generic usage flow for learners.

#. Learners have to download and install the official application (Google Play or App Store, we'll use Android version for examples).

#. Once installed there is initial one-time setup guide.

    .. image:: ../_static/images/verifiable_credentials-lcw-setup1.png
        :alt: Learner Credential Wallet setup step 1
        :width: 30%
    .. image:: ../_static/images/verifiable_credentials-lcw-setup2.png
        :alt: Learner Credential Wallet setup step 2
        :width: 30%
    .. image:: ../_static/images/verifiable_credentials-lcw-setup3.png
        :alt: Learner Credential Wallet setup step 3
        :width: 30%

#. Learners navigate Learner Record MFE interface (`Verifiable Credentials tab`_) and claim for a verifiable credential issuance (clicking a :guilabel:`Create` button).

#. On the next step learners are asked for QR code scanning - that's where the LCWallet app starts its flow. Learners use :guilabel:`Scan QR code` option in the mobile application.

    .. image:: ../_static/images/verifiable_credentials-lcw-home-empty.png
        :alt: Learner Credential Wallet empty
        :width: 30%
    .. image:: ../_static/images/verifiable_credentials-lcw-add-credential.png
        :alt: Learner Credential Wallet add credential
        :width: 30%
    .. image:: ../_static/images/verifiable_credentials-lcw-qrcode-scanner.png
        :alt: Learner Credential Wallet QR code scanner
        :width: 30%

#. LCWallet processes QR code, communicates with the Open edX Platform and gets new verifiable credential. If everything is correct, now digital wallet holds the verifiable credential for the given Open edX credential (program certificate).

    .. image:: ../_static/images/verifiable_credentials-lcw-accept-credential.png
        :alt: Learner Credential Wallet accept credential
        :width: 30%
    .. image:: ../_static/images/verifiable_credentials-lcw-credential-preview.png
        :alt: Learner Credential Wallet credential preview
        :width: 30%
    .. image:: ../_static/images/verifiable_credentials-lcw-verification-status.png
        :alt: Learner Credential Wallet credential status
        :width: 30%

#. From this point learners are free to share their achievements in different ways

    .. image:: ../_static/images/verifiable_credentials-lcw-share.png
        :alt: Learner Credential Wallet share credential
        :width: 30%
    .. image:: ../_static/images/verifiable_credentials-lcw-share-public-link.png
        :alt: Learner Credential Wallet share credential with public link
        :width: 30%
    .. image:: ../_static/images/verifiable_credentials-lcw-share-public-link-created.png
        :alt: Learner Credential Wallet shared with public link credential
        :width: 30%

.. code::

    # an example of a verifiable presentation being shared:
    {
    "@context": [
        "https://www.w3.org/2018/credentials/v1"
    ],
    "type": [
        "VerifiablePresentation"
    ],
    "verifiableCredential": [
        {
        "@context": [
            "https://www.w3.org/2018/credentials/v1",
            "https://w3id.org/security/suites/ed25519-2020/v1",
            "https://w3id.org/vc/status-list/2021/v1",
            "https://purl.imsglobal.org/spec/ob/v3p0/context.json"
        ],
        "id": "urn:uuid:7e33f82c-474b-4331-9cb7-71d2ace136e4",
        "type": [
            "VerifiableCredential",
            "OpenBadgeCredential"
        ],
        "credentialSubject": {
            "id": "did:key:z6MkoXpRTvd9KhEdbjaieR2XCs6XewVyW32dyKjG1GoPGNww",
            "name": "demo",
            "achievement": {
            "criteria": {
                "narrative": "Demo successfully completed all courses and received passing grades for a Professional Certificate in dcc program a program offered by , in collaboration with Open edX."
            },
            "description": "Program certificate is granted on program dcc program completion offered by , in collaboration with Open edX. The dcc program program includes 1 course(s).",
            "id": "31187856-01ac-4abc-9b77-4add9cf7c50b",
            "name": "Program certificate for passing a program dcc program",
            "type": "Achievement"
            },
            "type": "AchievementSubject"
        },
        "issuer": {
            "id": "did:key:z6MkkePoGJV8CQJJULSHHUEv71okD9PsrqXnZpNQuoUfb3id",
            "type": "Profile",
            "name": "Default verifiable credentials issuer"
        },
        "issuanceDate": "2023-07-10T15:25:41Z",
        "proof": {
            "type": "Ed25519Signature2020",
            "proofPurpose": "assertionMethod",
            "proofValue": "z5HRVyz1ZHUY7f8m6ttUS7JViKqwhFBWt2caEnauEAKmWs69ud93ok6AMrmfjZe1bLdrLcPusVNtNXCzwHXLaFJmJ",
            "verificationMethod": "did:key:z6MkkePoGJV8CQJJULSHHUEv71okD9PsrqXnZpNQuoUfb3id#z6MkkePoGJV8CQJJULSHHUEv71okD9PsrqXnZpNQuoUfb3id",
            "created": "2023-07-10T15:25:41.581Z"
        },
        "credentialStatus": {
            "id": "https://credentials.example.com/verifiable_credentials/api/v1/status-list/2021/v1/did:key:z6MkkePoGJV8CQJJULSHHUEv71okD9PsrqXnZpNQuoUfb3id/#6",
            "type": "StatusList2021Entry",
            "statusPurpose": "revocation",
            "statusListIndex": "6",
            "statusListCredential": "https://credentials.example.com/verifiable_credentials/api/v1/status-list/2021/v1/did:key:z6MkkePoGJV8CQJJULSHHUEv71okD9PsrqXnZpNQuoUfb3id/"
        },
        "name": "Program certificate for passing a program dcc program",
        "issued": "2023-07-10T15:25:41Z",
        "validFrom": "2023-07-10T15:25:41Z"
        }
    ]
    }

Other options
-------------

Additionally, you can install the `openedx-wallet`_ POC for investigation/onboarding purposes.  This wallet is not recommended for production deployment.

.. _Official web-site: https://lcw.app/
.. _Digital Credentials Consortium: https://digitalcredentials.mit.edu/
.. _community issuer registry: https://github.com/digitalcredentials/community-registry
.. _`Sandbox Registry`: https://github.com/digitalcredentials/sandbox-registry
.. _`Verifiable Credentials tab`: components.html#learner-record-microfrontend
.. _openedx-wallet: https://github.com/raccoongang/openedx-wallet