Configuring Certificates
========================

.. contents::
  :local:
  :depth: 2

Feature Toggling
----------------
All new features/functionality should be released behind a feature gate. This allows us to easily disable features
in the event that an issue is discovered in production. This project uses the
`Waffle <http://waffle.readthedocs.org/en/latest/>`_ library for feature gating.

Waffle supports three types of feature gates (listed below). We typically use flags and switches since samples are
random, and not ideal for our needs.

    Flag
        Enable a feature for specific users, groups, users meeting certain criteria (e.g. authenticated or staff),
        or a certain percentage of visitors.

    Switch
        Simple boolean, toggling a feature for all users.

    Sample
        Toggle the feature for a specified percentage of the time.


For information on creating or updating features, refer to the
`Waffle documentation <http://waffle.readthedocs.org/en/latest/>`_.

Permanent Feature Rollout
~~~~~~~~~~~~~~~~~~~~~~~~~
Over time some features may become permanent and no longer need a feature gate around them. In such instances, the
relevant code and tests should be updated to remove the feature gate. Once the code is released, the feature flag/switch
should be deleted.


Enabling Hours of Effort
------------------------
To display the hours of effort for a program on the program certificate, follow these steps.

.. note:: To show Hours of Effort, the Total hours of effort field must have a value for a program set in the Discovery Django Admin at **Home** › **Course Metadata** › **Programs**. If this field has no value, Hours of Effort will not be displayed on the certificate.

#. Log in to the Credentials Django administration (``{credentials_base_url}/admin``).

#. On the **Site Administration** page, locate **Credentials** and select **Program certificate configurations**.

#. Create or update the Program certificate configuration you would like to enable Hours of Effort for.

#. Select the **Include hours of effort** checkbox.

#. Select **Save**. Program certificates generated after this change will include Hours of Effort.


