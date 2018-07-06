Catalog Integration
===================

This Django app contains the models and management commands to sync with
the Discovery catalog service and store a copy of that information
locally.

Credentials specifics
---------------------

This is probably a task that lots of IDAs want to do. If we ever want to
make this app more generic, here are the Credentials-specific callouts
to be aware of:

-  We only keep and sync the models we care about.
-  We only keep and sync the model fields we care about.
-  In the management command, we grab the discovery URL from the site
   config in a way that is Credentials-specific.
