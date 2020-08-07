from django.apps import AppConfig


class CoreAppConfig(AppConfig):
    name = 'credentials.apps.core'
    verbose_name = 'Core'

    def ready(self):
        super().ready()

        # noinspection PyUnresolvedReferences
        import credentials.apps.core.signals  # pylint: disable=unused-import, import-outside-toplevel
