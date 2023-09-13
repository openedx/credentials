LMS User ID
===========

According to `OEP-32`_, The **LMS_USER_ID** is now the standard for uniquely identifying users within an Open edX system. The credentials service has a column on the **CORE_USER** table (called **LMS_USER_ID**). This column will automatically populate in the following contexts for new users:

#. If a user is awarded a credential by the LMS, when credentials is notified, a user in the **CORE_USER** table is created. The **LMS_USER_ID** will now also be populated.
#. If a user logs into the system, and navigates to their record page, if a user does not already exist for them in the credentials service, one will be created and the **LMS_USER_ID** will be populated.
#. If the system is configured to use the event bus to consume (course) ``CERTIFICATE_CREATED`` events, and if the user doesn't exist in Credentials yet, a user in the **CORE_USER** table is created. The **LMS_USER_ID** will be populated.

Backpopulating Pre-existing users
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
Although new users interacting with the system will automatically have this column populated, users who already exist in the system will not.

For those users, a `management command`_ exists to backpopulate the data. This management command utilizes endpoints in the LMS to retrieve and sync missing ids for learners in Credentials.

.. _OEP-32: https://open-edx-proposals.readthedocs.io/en/latest/oep-0032-arch-unique-identifier-for-users.html
.. _management command: https://github.com/openedx/credentials/blob/master/credentials/apps/core/management/commands/sync_ids_from_platform.py
.. _required for that user to have the **LMS_USER_ID**: https://github.com/openedx/credentials/blob/b5ceeaceaea23ba209510b0bafa4404e26ce87c9/credentials/apps/credentials/issuers.py#L183
