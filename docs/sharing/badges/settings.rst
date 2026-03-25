.. _badges-settings:

Badging Settings
=================

These settings control the Badges feature: availability, event subscriptions, and provider integration (Credly, Accredible).

.. tip::

   The `tutor-contrib-badges`_ plugin configures all required settings automatically. The reference below is for manual or customized deployments.

.. _tutor-contrib-badges: https://github.com/raccoongang/tutor-contrib-badges


Feature Switch
--------------

The Badges feature is disabled by default. Enable it in both services.

.. code-block:: python

   # openedx-platform (LMS) settings:
   FEATURES["BADGES_ENABLED"] = True

   # Credentials service settings:
   BADGES_ENABLED = True


``BADGES_CONFIG`` Reference
----------------------------

``BADGES_CONFIG`` is the main configuration dictionary for the Credentials service.

.. code-block:: python

   BADGES_CONFIG = {
       "events": [
           "org.openedx.learning.course.passing.status.updated.v1",
           "org.openedx.learning.ccx.course.passing.status.updated.v1",
       ],
       "credly": {
           "CREDLY_BASE_URL": "https://credly.com/",
           "CREDLY_API_BASE_URL": "https://api.credly.com/v1/",
           "CREDLY_SANDBOX_BASE_URL": "https://sandbox.credly.com/",
           "CREDLY_SANDBOX_API_BASE_URL": "https://sandbox-api.credly.com/v1/",
           "USE_SANDBOX": False,
       },
       "accredible": {
           "ACCREDIBLE_BASE_URL": "https://dashboard.accredible.com/",
           "ACCREDIBLE_API_BASE_URL": "https://api.accredible.com/v1/",
           "ACCREDIBLE_SANDBOX_BASE_URL": "https://sandbox.dashboard.accredible.com/",
           "ACCREDIBLE_SANDBOX_API_BASE_URL": "https://sandbox.api.accredible.com/v1/",
           "USE_SANDBOX": False,
       },
       "rules": {
           "ignored_keypaths": [
               "user.id",
               "user.is_active",
               "user.pii.username",
               "user.pii.email",
               "user.pii.name",
               "course.display_name",
               "course.start",
               "course.end",
           ],
       },
   }

Top-level keys
~~~~~~~~~~~~~~

.. list-table::
   :header-rows: 1
   :widths: 25 75

   * - Key
     - Description
   * - ``events``
     - Event bus signals available for requirements and penalties. Only events whose payload includes learner PII (``UserData``) are applicable.
   * - ``credly``
     - Credly provider URLs and sandbox toggle (see below).
   * - ``accredible``
     - Accredible provider URLs and sandbox toggle (see below).
   * - ``rules.ignored_keypaths``
     - Event payload paths excluded from data rule options in the admin UI (see :ref:`badges-configuration`).

Credly Settings
~~~~~~~~~~~~~~~

.. list-table::
   :header-rows: 1
   :widths: 35 65

   * - Setting
     - Description
   * - ``USE_SANDBOX``
     - Use Credly sandbox environment for development and testing.
   * - ``CREDLY_BASE_URL``
     - Credly production host URL.
   * - ``CREDLY_API_BASE_URL``
     - Credly production API URL.
   * - ``CREDLY_SANDBOX_BASE_URL``
     - Credly sandbox host URL.
   * - ``CREDLY_SANDBOX_API_BASE_URL``
     - Credly sandbox API URL.

Accredible Settings
~~~~~~~~~~~~~~~~~~~

.. list-table::
   :header-rows: 1
   :widths: 35 65

   * - Setting
     - Description
   * - ``USE_SANDBOX``
     - Use Accredible sandbox environment for development and testing.
   * - ``ACCREDIBLE_BASE_URL``
     - Accredible production host URL.
   * - ``ACCREDIBLE_API_BASE_URL``
     - Accredible production API URL.
   * - ``ACCREDIBLE_SANDBOX_BASE_URL``
     - Accredible sandbox host URL.
   * - ``ACCREDIBLE_SANDBOX_API_BASE_URL``
     - Accredible sandbox API URL.


Event Bus Configuration
-----------------------

.. tip::

   If you use the `tutor-contrib-badges`_ plugin, event bus configuration is handled automatically. This section is for custom deployments.

All badge-related events use the ``learning-badges-lifecycle`` topic.

Source Signals (LMS)
~~~~~~~~~~~~~~~~~~~~

The LMS produces two signals that trigger badge processing.

.. list-table::
   :header-rows: 1
   :widths: 55 45

   * - Signal
     - Purpose
   * - ``org.openedx.learning.course.passing.status.updated.v1``
     - Course grade updated - enables course completion recognition.
   * - ``org.openedx.learning.ccx.course.passing.status.updated.v1``
     - CCX course grade updated - enables CCX course completion recognition.

.. code-block:: python

   # openedx-platform (LMS) settings:
   EVENT_BUS_PRODUCER_CONFIG = {
       ...
       "org.openedx.learning.course.passing.status.updated.v1": {
           "learning-badges-lifecycle": {
               "event_key_field": "course_passing_status.course.course_key",
               "enabled": _should_send_learning_badge_events,
           },
       },
       "org.openedx.learning.ccx.course.passing.status.updated.v1": {
           "learning-badges-lifecycle": {
               "event_key_field": "course_passing_status.course.course_key",
               "enabled": _should_send_learning_badge_events,
           },
       },
   }

Emitted Signals (Credentials)
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

The Credentials service emits two signals after badge processing completes.

.. list-table::
   :header-rows: 1
   :widths: 55 45

   * - Signal
     - Purpose
   * - ``org.openedx.learning.badge.awarded.v1``
     - A badge was awarded to a learner.
   * - ``org.openedx.learning.badge.revoked.v1``
     - A badge was revoked from a learner.

.. code-block:: python

   # Credentials service settings:
   EVENT_BUS_PRODUCER_CONFIG = {
       ...
       "org.openedx.learning.badge.awarded.v1": {
           "learning-badges-lifecycle": {
               "event_key_field": "badge.uuid",
               "enabled": BADGES_ENABLED,
           },
       },
       "org.openedx.learning.badge.revoked.v1": {
           "learning-badges-lifecycle": {
               "event_key_field": "badge.uuid",
               "enabled": BADGES_ENABLED,
           },
       },
   }

These signals are only produced when ``BADGES_ENABLED`` is ``True``.

Consumer Setup
~~~~~~~~~~~~~~

The consumer implementation depends on your event bus backend (Redis Streams, Kafka, etc.).

Both the Credentials and LMS services **produce** messages to the event stream. A separate **consumer** process pulls and handles those messages.

**Redis Streams** - uses the event-bus-redis_ package, which provides a Django management command.

.. code-block:: bash

   # Run in the Credentials service (required for badge processing):
   ./manage.py consume_events \
       -t learning-badges-lifecycle \
       -g credentials_dev \
       --extra='{"consumer_name": "credentials_dev.consumer1"}'

   # Run in the openedx-platform (LMS) (optional - only if LMS needs badge award/revoke notifications):
   ./manage.py lms consume_events \
       -t learning-badges-lifecycle \
       -g lms_dev \
       --extra='{"consumer_name": "lms_dev.consumer1"}'

.. important::

   The **Credentials consumer** is required - it processes all incoming badge events. The **LMS consumer** is optional and only needed if LMS should react to badge award or revocation signals.


.. _event-bus-redis: https://github.com/openedx/event-bus-redis
