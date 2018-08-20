Pathways
========
Pathways represent channels where learners can send their program records to institutions for credit or other
reasons.  Pathways can be either professional, or for credit, but they are mostly used as credit pathways in
credentials.

Creation
--------
Pathways get created in the course-discovery_ admin.
Credentials receives these pathways by calling the ``copy_catalog`` management command.

.. _course-discovery: https://github.com/edx/course-discovery

Sending Learner Records
-----------------------
Credit pathways appear in the Send Learner Record modal on the program record page.
This modal shows each pathway associated with program, with the requirement that the pathway has an email address.
If no pathways exist with an email address, the Send Learner Record button will not be visible.

When a learner sends their program record to a credit pathway, an email is sent to the pathway's email address using edx-ace_.
This email contains information about the record, a link to the public record, and a link to download the csv data.

After an email is sent, a ``UserCreditPathway`` object is created to prevent the learner from sending the same record to the
same pathway again. This is done by disabling the pathway's checkbox and adding text to it indicating to the user that the record has been sent.

.. _edx-ace: https://github.com/edx/edx-ace

Source Email Address
--------------------
By default, the "from" address of the email will be "no-reply@[SITE DOMAIN]. This email address can be modified by setting
the partner_from_address field of the site configuration, in which case that will be used.

Email Sending Errors
--------------------
If an email fails to send, an alert will appear on the screen. Note that this only indicates if the POST request to send the email fails, it does not show whether edx-ace successfully sent the email.
If an issue actually sending the email itself occurs, it will bounce back to the source email address.
