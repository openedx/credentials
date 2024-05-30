from django.apps import AppConfig

from credentials.apps.badges.toggles import check_badges_enabled


class BadgesConfig(AppConfig):
    """
    Core badges application configuration.
    """

    name = "credentials.apps.badges"
    plugin_label = "badges"
    verbose_name = "Badges"

    @check_badges_enabled
    def ready(self):
        """
        Activate installed badges plugins if they are enabled.

        Performs initial registrations for checks, signals, etc.
        """
        from credentials.apps.badges import signals  # pylint: disable=unused-import,import-outside-toplevel
        from credentials.apps.badges.checks import (  # pylint: disable=unused-import,import-outside-toplevel
            badges_checks,
        )
        from credentials.apps.badges.signals.handlers import (  # pylint: disable=import-outside-toplevel
            listen_to_badging_events,
        )

        listen_to_badging_events()

        super().ready()
