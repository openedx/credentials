User Credential Date Override
=============================

Status
------
Accepted

Background
----------
The ability to override the “Issued” date on a course certificate has been added
to edx-platform. Credentials cares about a course certificate’s date for display
on the Program Record page. If we want the “Date Earned” column on a learner’s
Program Record page to match the date on their course certificate when a date
override is present, Credentials needs to receive, store, and use the date
override value.

Decision
--------
Make a new model in Credentials called ``UserCredentialDateOverride``. This will
have a ``OneToOne`` relationship with ``UserCredential`` and will generally
mirror the relationship that ``CertificateDateOverride`` and
``GeneratedCertificate`` have in edx-platform.

When a post from edx-platform sends certificate data, it will include a
``date_override`` key. If a value is sent, Credentials will make a new
``UserCredentialDateOverride`` for the given credential, or else update the
relevant ``UserCredentialDateOverride`` if one already exists for the
credential. If no value for ``date_override`` is sent, Credentials will delete
any existing ``UserCredentialDateOverride`` associated with the given
credential, if present.

At the time of this writing, the ``UserCredentialDateOverride`` will be used
solely for course credentials, and solely for display in the “Date Earned”
column on the Program Records page. It will not affect the program credential
“Issue” date, or affect when a program credential (or other information, like
program records) becomes visible/available.
