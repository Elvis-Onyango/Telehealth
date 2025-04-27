from django.apps import AppConfig
from . import signals


class AppointmentsConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'apps.appointments'
    def ready(self):
        signals  # Ensure signals are loaded