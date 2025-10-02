"""
Конфигурация приложения flights для работы с полетами БАС.
"""

from django.apps import AppConfig


class FlightsConfig(AppConfig):
    """Конфигурация приложения flights."""

    default_auto_field = "django.db.models.BigAutoField"
    name = "apps.flights"
    verbose_name = "Полеты БАС"
