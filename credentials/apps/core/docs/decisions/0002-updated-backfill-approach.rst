LMS User Id Backfill in the Credentials IDA
===========================================

Status
------
Draft

Background
----------

In ADR-0001, the backfill was abandoned because of technical difficulties and a lack of immediate need for lms user ids. Recently a new endpoint was added to Credentials that allows searching for a learner's completion status, which can take an lms user id as an identifier.

The technical challenges still remain, but a new management command has been created which will synchronize the missing lms user ids in Credentials.

Decision
--------

The old sync_lms_user_ids management command will be removed, and will be functionally replaced by the `sync_ids_from_platform` management command.
The learner ids will be updated to enable fetching learner status by lms user id.

