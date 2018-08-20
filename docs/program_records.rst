Program Records
===============
Program records are how learners can view and share their achievements in a given program.

Views
-----

A learner can see a list of their own program records at ``/records/`` which then links to specific program records under ``/records/programs/<uuid>``.

If you are a staff user, you can masquerade as a specific learner (see the pages as that user sees them) by using the banner that appears at the top of the records pages.

A learner must be logged in to view these pages.

The list of records is linked to from the LMS under each learnerʼs profile.
Each specific program record is linked to from the LMS under that programʼs progress dashboard page.

Creation
--------

Program Records donʼt have a concrete representation in the database.
Rather, the view for a record is created when the LMS tells the Credentials IDA that a course certificate has been awarded in a program.
That — plus grade information (also sent by the LMS) — gets used to display records pages to the learner.

Configuration
-------------

Records are enabled by default.
But you can disable support for the records feature by toggling the ``Enable Records`` checkbox in a given site configuration.
This will disable the views from appearing and will stop the ``copy_catalog`` job from saving catalog data for that site.

Additionally, you will want to disable a similar site configuration toggle on the LMS side, so that it will stop sending records data to Credentials.

Also make sure that the ``copy_catalog`` job is run periodically.
It pulls in all the required program catalog data from the Discovery IDA.

Backpopulation
--------------

If for whatever reason, you need to backpopulate records data (maybe there was a service outage, or you just enabled records support for a site), you will want to run the LMS management command ``notify_credentials``.
Look at its LMS documentation to see your options.

Sharing
-------

If a learner decides to share a program record, a new URL is created for a public version of that record.
Anyone with that link can view the record, without needing to be logged in.

In addition to the web view of the record, there is a download button for a CSV version of the data.

Currently, there is no user management of the shared record.
The only way to stop sharing a record is to have an admin delete the recordʼs entry in the ``ProgramCertRecord`` model.

Sending For Credit
------------------

A learner can also choose to send the record to a site partner, to receive credit from that partner for the earned certificates.

Note that this merely sends an email to the partner so they can see the record.
Each partner will have their own process for initiating or processing a credit request, of which viewing a learnerʼs record is one small part.

Read the :doc:`pathways <pathways>` documentation for more information on how to enable and configure requesting credit.

If no credit pathways are enabled for a given program, the ``Send Learner Record`` button will not appear on that programʼs records.
