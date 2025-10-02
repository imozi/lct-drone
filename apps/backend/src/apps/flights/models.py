"""
Модели для работы с полетами беспилотных авиационных систем (БАС).
"""

import re

from django.contrib.gis.db import models
from django.contrib.gis.geos import Point
from django.core.validators import RegexValidator
from django.utils.translation import gettext_lazy as _

from core.models import BaseModel


class RussianRegion(BaseModel):
    """Модель для хранения субъектов Российской Федерации."""

    name = models.CharField(
        _("Название"),
        max_length=255,
        help_text=_("Название субъекта РФ"),
    )

    code = models.CharField(
        _("Код региона"),
        max_length=10,
        unique=True,
        help_text=_("Официальный код субъекта РФ"),
    )

    okato = models.CharField(
        _("ОКАТО код"),
        max_length=10,
        blank=True,
        help_text=_("Код ОКАТО субъекта РФ"),
    )

    status = models.CharField(
        _("Статус"),
        max_length=50,
        blank=True,
        help_text=_("Статус субъекта (край, область, республика и т.д.)"),
    )

    utc = models.CharField(
        _("Часовой пояс UTC"),
        max_length=10,
        blank=True,
        help_text=_("Смещение относительно UTC (например, +3, +7)"),
    )

    timezone = models.CharField(
        _("Timezone"),
        max_length=50,
        blank=True,
        help_text=_("Название часового пояса (например, Europe/Moscow)"),
    )

    area = models.CharField(
        _("Area"),
        max_length=50,
        blank=True,
        help_text=_("Площадь региона, в км2"),
    )

    geometry = models.MultiPolygonField(
        _("Геометрия"),
        help_text=_("Геометрические границы региона"),
        null=True,
        blank=True,
    )

    class Meta:
        verbose_name = _("Субъект РФ")
        verbose_name_plural = _("Субъекты РФ")
        ordering = ["name"]
        indexes = [
            models.Index(fields=["code"]),
            models.Index(fields=["name"]),
        ]

    def __str__(self) -> str:
        return self.name


class RussianRegionWithWater(BaseModel):
    """Модель для хранения субъектов Российской Федерации."""

    name = models.CharField(
        _("Название"),
        max_length=255,
        help_text=_("Название субъекта РФ"),
    )

    code = models.CharField(
        _("Код региона"),
        max_length=10,
        unique=True,
        help_text=_("Официальный код субъекта РФ"),
    )

    okato = models.CharField(
        _("ОКАТО код"),
        max_length=10,
        blank=True,
        help_text=_("Код ОКАТО субъекта РФ"),
    )

    status = models.CharField(
        _("Статус"),
        max_length=50,
        blank=True,
        help_text=_("Статус субъекта (край, область, республика и т.д.)"),
    )

    utc = models.CharField(
        _("Часовой пояс UTC"),
        max_length=10,
        blank=True,
        help_text=_("Смещение относительно UTC (например, +3, +7)"),
    )

    timezone = models.CharField(
        _("Timezone"),
        max_length=50,
        blank=True,
        help_text=_("Название часового пояса (например, Europe/Moscow)"),
    )

    geometry = models.MultiPolygonField(
        _("Геометрия"),
        help_text=_("Геометрические границы региона"),
        null=True,
        blank=True,
    )

    class Meta:
        verbose_name = _("Субъект РФ c водной границей")
        verbose_name_plural = _("Субъекты РФ c водной границей")
        ordering = ["name"]
        indexes = [
            models.Index(fields=["code"]),
            models.Index(fields=["name"]),
        ]

    def __str__(self) -> str:
        return self.name


class DroneOperator(BaseModel):
    """Модель оператора БАС."""

    name = models.CharField(
        _("Название"),
        max_length=500,
        help_text=_("Название организации или ФИО оператора"),
    )

    phone = models.CharField(
        _("Телефон"),
        max_length=20,
        blank=True,
        validators=[
            RegexValidator(
                regex=r"^\+?[0-9\-\(\)\s]{7,20}$",
                message=_("Некорректный формат номера телефона"),
            )
        ],
        help_text=_("Контактный телефон оператора"),
    )

    organization_type = models.CharField(
        _("Тип организации"),
        max_length=200,
        blank=True,
        help_text=_("МВД, МЧС, коммерческая организация и т.д."),
    )

    class Meta:
        verbose_name = _("Оператор БАС")
        verbose_name_plural = _("Операторы БАС")
        ordering = ["name"]
        indexes = [
            models.Index(fields=["name"]),
            models.Index(fields=["organization_type"]),
        ]

    def __str__(self) -> str:
        return self.name


class DroneType(BaseModel):
    """Модель типа БАС."""

    code = models.CharField(
        _("Код типа"),
        max_length=10,
        unique=True,
        help_text=_("Код типа БАС (например, BLA, AER)"),
    )

    name = models.CharField(
        _("Название"),
        max_length=200,
        help_text=_("Полное название типа БАС"),
    )

    description = models.TextField(
        _("Описание"),
        blank=True,
        help_text=_("Дополнительная информация о типе БАС"),
    )

    class Meta:
        verbose_name = _("Тип БАС")
        verbose_name_plural = _("Типы БАС")
        ordering = ["code"]
        indexes = [
            models.Index(fields=["code"]),
        ]

    def __str__(self) -> str:
        return f"{self.code} - {self.name}"


class FlightZone(BaseModel):
    """Модель зоны полета."""

    code = models.CharField(
        _("Код зоны"),
        max_length=50,
        help_text=_("Код зоны полета (например, WR299, KO02)"),
    )

    name = models.CharField(
        _("Название зоны"),
        max_length=200,
        blank=True,
        help_text=_("Название зоны полета"),
    )

    geometry = models.PolygonField(
        _("Геометрия зоны"),
        null=True,
        blank=True,
        help_text=_("Геометрические границы зоны полета"),
    )

    class Meta:
        verbose_name = _("Зона полета")
        verbose_name_plural = _("Зоны полетов")
        ordering = ["code"]
        indexes = [
            models.Index(fields=["code"]),
        ]

    def __str__(self) -> str:
        return self.code


class FlightPlan(BaseModel):
    """Модель плана полета БАС (данные из столбца SHR)."""

    # Основные идентификаторы
    flight_id = models.CharField(
        _("ID полета"),
        max_length=50,
        help_text=_("Уникальный идентификатор плана полета"),
    )

    sid = models.CharField(
        _("SID"),
        max_length=20,
        help_text=_("Системный идентификатор"),
    )

    reg_number = models.CharField(
        _("Регистрационный номер БАС"),
        max_length=50,
        blank=True,
        help_text=_("Регистрационный номер БАС"),
    )

    # Временные данные
    planned_date = models.DateField(
        _("Плановая дата полета"),
        help_text=_("Плановая дата полета"),
    )

    planned_departure_time = models.TimeField(
        _("Плановое время вылета"),
        help_text=_("Плановое время вылета по UTC"),
    )

    planned_duration = models.DurationField(
        _("Плановая продолжительность"),
        help_text=_("Плановая продолжительность полета"),
    )

    # Высотные данные
    min_altitude = models.IntegerField(
        _("Минимальная высота"),
        default=0,
        help_text=_("Минимальная высота полета в метрах"),
    )

    max_altitude = models.IntegerField(
        _("Максимальная высота"),
        default=0,
        help_text=_("Максимальная высота полета в метрах"),
    )

    # Геопространственные данные
    departure_point = models.PointField(
        _("Точка вылета"),
        help_text=_("Координаты точки вылета"),
    )

    destination_point = models.PointField(
        _("Точка назначения"),
        help_text=_("Координаты точки назначения"),
    )

    # Связи с другими моделями
    operator = models.ForeignKey(
        DroneOperator,
        on_delete=models.CASCADE,
        verbose_name=_("Оператор"),
        help_text=_("Оператор БАС"),
    )

    drone_type = models.ForeignKey(
        DroneType,
        on_delete=models.CASCADE,
        verbose_name=_("Тип БАС"),
        help_text=_("Тип беспилотной авиационной системы"),
    )

    flight_zone = models.ForeignKey(
        FlightZone,
        on_delete=models.CASCADE,
        verbose_name=_("Зона полета"),
        help_text=_("Зона полета"),
        null=True,
        blank=True,
    )

    departure_region = models.ForeignKey(
        RussianRegion,
        on_delete=models.CASCADE,
        related_name="departure_flights",
        verbose_name=_("Регион вылета"),
        help_text=_("Регион, откуда выполняется вылет"),
        null=True,
        blank=True,
    )

    destination_region = models.ForeignKey(
        RussianRegion,
        on_delete=models.CASCADE,
        related_name="destination_flights",
        verbose_name=_("Регион назначения"),
        help_text=_("Регион назначения"),
        null=True,
        blank=True,
    )

    # Дополнительные данные
    purpose = models.TextField(
        _("Цель полета"),
        blank=True,
        help_text=_("Цель и описание полета"),
    )

    special_conditions = models.TextField(
        _("Особые условия"),
        blank=True,
        help_text=_("Особые условия полета и ограничения"),
    )

    raw_data = models.JSONField(
        _("Исходные данные"),
        default=dict,
        blank=True,
        help_text=_("Исходные неструктурированные данные из файла"),
    )

    class Meta:
        verbose_name = _("План полета")
        verbose_name_plural = _("Планы полетов")
        ordering = ["-planned_date", "-planned_departure_time"]
        indexes = [
            models.Index(fields=["flight_id"]),
            models.Index(fields=["sid"]),
            models.Index(fields=["planned_date"]),
            models.Index(fields=["departure_point"]),
            models.Index(fields=["destination_point"]),
            models.Index(fields=["operator"]),
            models.Index(fields=["drone_type"]),
            models.Index(fields=["departure_region"]),
        ]

    def __str__(self) -> str:
        return f"План полета {self.flight_id} ({self.planned_date})"

    @staticmethod
    def parse_coordinates(coord_str: str) -> Point | None:
        """
        Парсинг координат из формата DMS в десятичные градусы.

        Args:
            coord_str: Строка координат в формате "5525N03716E"

        Returns:
            Point с координатами в десятичных градусах или None
        """
        if not coord_str:
            return None

        # Паттерн для парсинга координат в формате DDMMN/SDDDMME/W
        pattern = r"(\d{2})(\d{2})([NS])(\d{3})(\d{2})([EW])"
        match = re.match(pattern, coord_str.replace("/", ""))

        if not match:
            return None

        lat_deg, lat_min, lat_dir, lon_deg, lon_min, lon_dir = match.groups()

        # Конвертация в десятичные градусы
        latitude = float(lat_deg) + float(lat_min) / 60
        longitude = float(lon_deg) + float(lon_min) / 60

        # Применение направления
        if lat_dir == "S":
            latitude = -latitude
        if lon_dir == "W":
            longitude = -longitude

        return Point(longitude, latitude)

    @staticmethod
    def parse_time(time_str: str) -> str | None:
        """
        Парсинг времени из формата HHMM в HH:MM.

        Args:
            time_str: Строка времени в формате "0700"

        Returns:
            Время в формате "HH:MM" или None
        """
        if not time_str or len(time_str) != 4:
            return None

        try:
            hours = int(time_str[:2])
            minutes = int(time_str[2:])

            if 0 <= hours <= 23 and 0 <= minutes <= 59:
                return f"{hours:02d}:{minutes:02d}"
        except ValueError:
            pass

        return None

    def save(self, *args, **kwargs):
        """Автоматическая геопривязка к регионам при сохранении."""
        super().save(*args, **kwargs)

        regions_updated = False
        update_fields = []

        # Определение региона вылета
        if self.departure_point and not self.departure_region:
            departure_region = (
                RussianRegion.objects.filter(geometry__contains=self.departure_point)
                .select_related()
                .first()
            )
            if departure_region:
                self.departure_region = departure_region
                regions_updated = True
                update_fields.append("departure_region")

        # Определение региона назначения
        if self.destination_point and not self.destination_region:
            destination_region = (
                RussianRegion.objects.filter(geometry__contains=self.destination_point)
                .select_related()
                .first()
            )
            if destination_region:
                self.destination_region = destination_region
                regions_updated = True
                update_fields.append("destination_region")

        # Повторное сохранение если были изменения в регионах
        if regions_updated and hasattr(self, "_state") and not self._state.adding:
            super().save(update_fields=update_fields)


class ActualFlight(BaseModel):
    """Модель фактического полета БАС (данные из столбцов DEP и ARR)."""

    # Связь с планом полета
    flight_plan = models.OneToOneField(
        FlightPlan,
        on_delete=models.CASCADE,
        verbose_name=_("План полета"),
        help_text=_("Связанный план полета"),
    )

    # Фактические данные вылета (DEP)
    actual_departure_date = models.DateField(
        _("Фактическая дата вылета"),
        null=True,
        blank=True,
        help_text=_("Фактическая дата вылета"),
    )

    actual_departure_time = models.TimeField(
        _("Фактическое время вылета"),
        null=True,
        blank=True,
        help_text=_("Фактическое время вылета по UTC"),
    )

    actual_departure_point = models.PointField(
        _("Фактическая точка вылета"),
        null=True,
        blank=True,
        help_text=_("Фактические координаты вылета"),
    )

    # Фактические данные прибытия (ARR)
    actual_arrival_date = models.DateField(
        _("Фактическая дата прибытия"),
        null=True,
        blank=True,
        help_text=_("Фактическая дата прибытия"),
    )

    actual_arrival_time = models.TimeField(
        _("Фактическое время прибытия"),
        null=True,
        blank=True,
        help_text=_("Фактическое время прибытия по UTC"),
    )

    actual_destination_point = models.PointField(
        _("Фактическая точка прибытия"),
        null=True,
        blank=True,
        help_text=_("Фактические координаты прибытия"),
    )

    # Расчетные поля
    actual_duration = models.DurationField(
        _("Фактическая продолжительность"),
        null=True,
        blank=True,
        help_text=_("Фактическая продолжительность полета"),
    )

    flight_status = models.CharField(
        _("Статус полета"),
        max_length=20,
        choices=[
            ("planned", _("Запланирован")),
            ("departed", _("Вылетел")),
            ("completed", _("Завершен")),
            ("cancelled", _("Отменен")),
        ],
        default="planned",
        help_text=_("Статус выполнения полета"),
    )

    class Meta:
        verbose_name = _("Фактический полет")
        verbose_name_plural = _("Фактические полеты")
        ordering = ["-actual_departure_date", "-actual_departure_time"]
        indexes = [
            models.Index(fields=["actual_departure_date"]),
            models.Index(fields=["flight_status"]),
            models.Index(fields=["flight_plan"]),
        ]

    def __str__(self) -> str:
        return f"План полета SID: {self.flight_plan.sid}"

    def calculate_duration(self) -> str | None:
        """Расчет фактической продолжительности полета."""
        if (
            self.actual_departure_date
            and self.actual_departure_time
            and self.actual_arrival_date
            and self.actual_arrival_time
        ):

            from datetime import datetime, timedelta

            # Создание datetime объектов
            departure_datetime = datetime.combine(
                self.actual_departure_date, self.actual_departure_time
            )
            arrival_datetime = datetime.combine(
                self.actual_arrival_date, self.actual_arrival_time
            )

            # Если прилет на следующий день
            if arrival_datetime < departure_datetime:
                arrival_datetime += timedelta(days=1)

            duration = arrival_datetime - departure_datetime
            return duration

        return None

    def save(self, *args, **kwargs):
        """Автоматический расчет продолжительности и статуса при сохранении."""
        # Расчет продолжительности
        if not self.actual_duration:
            self.actual_duration = self.calculate_duration()

        # Определение статуса
        if self.actual_arrival_date and self.actual_arrival_time:
            self.flight_status = "completed"
        elif self.actual_departure_date and self.actual_departure_time:
            self.flight_status = "departed"
        else:
            self.flight_status = "planned"

        super().save(*args, **kwargs)


class FlightStatistics(BaseModel):
    """Модель для хранения агрегированной статистики полетов."""

    region = models.ForeignKey(
        RussianRegion,
        on_delete=models.CASCADE,
        verbose_name=_("Регион"),
        help_text=_("Регион для статистики"),
    )

    date = models.DateField(
        _("Дата"),
        help_text=_("Дата для статистики"),
    )

    planned_flights_count = models.IntegerField(
        _("Количество запланированных полетов"),
        default=0,
        help_text=_("Количество запланированных полетов за день"),
    )

    completed_flights_count = models.IntegerField(
        _("Количество завершенных полетов"),
        default=0,
        help_text=_("Количество завершенных полетов за день"),
    )

    total_flight_time = models.DurationField(
        _("Общее время полетов"),
        null=True,
        blank=True,
        help_text=_("Общее время всех полетов за день"),
    )

    unique_operators_count = models.IntegerField(
        _("Количество уникальных операторов"),
        default=0,
        help_text=_("Количество уникальных операторов за день"),
    )

    class Meta:
        verbose_name = _("Статистика полетов")
        verbose_name_plural = _("Статистика полетов")
        unique_together = ["region", "date"]
        ordering = ["-date", "region__name"]
        indexes = [
            models.Index(fields=["date"]),
            models.Index(fields=["region", "date"]),
        ]

    def __str__(self) -> str:
        return f"Статистика {self.region.name} за {self.date}"
