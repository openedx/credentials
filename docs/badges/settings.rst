Settings
========

.. note::

    You can find technical details on how to set up proper configurations for badges to be active in this section.

Badges feature settings allow configuration:

1. feature availability;
2. event bus public signals subset for badges;
3. the Credly service integration details (URLs, sandbox usage, etc.);


Feature switch
--------------

The Badges feature is under a feature switch (disabled by default).

To enable the feature, update these settings as follows:

.. code-block:: python

    # Platform services settings:
    FEATURES["BADGES_ENABLED"] = True

    # Credentials service settings:
    BADGES_ENABLED = True


Default settings
----------------

The feature has its configuration:

.. code-block:: python

    # Credentials settings:
    BADGES_CONFIG = {
        # these events become available in requirements/penalties setup:
        "events": [
            "org.openedx.learning.course.passing.status.updated.v1",
            "org.openedx.learning.ccx.course.passing.status.updated.v1",
        ],
        # Credly integration:
        "credly": {
            "CREDLY_BASE_URL": "https://credly.com/",
            "CREDLY_API_BASE_URL": "https://api.credly.com/v1/",
            "CREDLY_SANDBOX_BASE_URL": "https://sandbox.credly.com/",
            "CREDLY_SANDBOX_API_BASE_URL": "https://sandbox-api.credly.com/v1/",
            "USE_SANDBOX": False,
        },
        # requirements data rules:
        "rules": {
            "ignored_keypaths": [
                "user.id",
                "user.is_active",
                "user.pii.username",
                "user.pii.email",
                "user.pii.name",
            ],
        },
    }

- ``events`` - explicit event bus signals list (only events with PII user data in payload are applicable).
- ``credly`` - Credly integration details.
- ``rules.ignored_keypaths`` - event payload paths to exclude from data rule options (see: Configuration_).

Credly integration
~~~~~~~~~~~~~~~~~~

- USE_SANDBOX - enables Credly sandbox usage (development, testing);
- CREDLY_BASE_URL - Credly service host URL;
- CREDLY_API_BASE_URL - Credly API host URL;
- CREDLY_SANDBOX_BASE_URL - Credly sandbox host URL;
- CREDLY_SANDBOX_API_BASE_URL - Credly sandbox API host URL;


Event bus settings
------------------

    ``learning-badges-lifecycle`` is the event bus topic for all Badges related events.

The Badges feature has updated event bus producer configurations for the Platform and the Credentials services.

Source public signals
~~~~~~~~~~~~~~~~~~~~~

Platform's event bus producer configuration was extended with 2 public signals:

1. information about the fact someone’s course grade was updated (allows course completion recognition);
2. information about the fact someone’s CCX course grade was updated (allows CCX course completion recognition).

.. code-block:: python

    # Platform services settings:
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

Emitted public signals
~~~~~~~~~~~~~~~~~~~~~~

The Badges feature introduced 2 own event types:

1. information about the fact someone has earned a badge;
2. information about the fact someone's badge was revoked;

.. code-block:: python

    # Credentials service settings:
    EVENT_BUS_PRODUCER_CONFIG = {
        ...

        "org.openedx.learning.badge.awarded.v1": {
            "learning-badges-lifecycle": {"event_key_field": "badge.uuid", "enabled": True },
        },
        "org.openedx.learning.badge.revoked.v1": {
            "learning-badges-lifecycle": {"event_key_field": "badge.uuid", "enabled": True },
        },
    }

Consuming workers
~~~~~~~~~~~~~~~~~

.. note::

    Consumers implementation depends on the used event bus.

Event bus options:

- Redis Streams
- Kafka
- ...

The Credentials and the Platform services **produce** (push) their public signals as messages to the stream.

To **consume** (pull) those messages a consumer process is required.

Redis Streams
#############

When the Redis Streams event bus is used, the ``<preffix>-learning-badges-lifecycle`` stream is used for messages transport.

For producing and consuming a single package (broker) is used - event-bus-redis_.

"Event Bus Redis" is implemented as a Django application and provides a Django management command for consuming messages
(see all details in the package's README).

.. code-block:: bash

    # Credentials service consumer example:
    /edx/app/credentials/credentials/manage.py consume_events -t learning-badges-lifecycle -g credentials_dev --extra={"consumer_name":"credentials_dev.consumer1"}

    # LMS service consumer example:
    /edx/app/edxapp/edx-platform/manage.py lms consume_events -t learning-badges-lifecycle -g lms_dev --extra={"consumer_name":"lms_dev.consumer1"}

.. note::

    **Credentials event bus consumer** is crucial for the Badges feature, since it is responsible for all incoming events processing.

    **LMS event bus consumer** is only required if LMS wants to receive information about badges processing results (awarding/revocation).


.. _Configuration: configuration.html
.. _event-bus-redis: https://github.com/openedx/event-bus-redis