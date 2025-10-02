"""
Фильтры для API приложения flights.
"""

import django_filters
from django.contrib.gis.geos import Point
from django.contrib.gis.measure import Distance

from .models import ActualFlight, FlightPlan, FlightStatistics


class FlightPlanFilter(django_filters.FilterSet):
    """Фильтры для планов полетов."""

    # Фильтры по дате
    planned_date = django_filters.DateFilter()
    planned_date__gte = django_filters.DateFilter(
        field_name="planned_date", lookup_expr="gte"
    )
    planned_date__lte = django_filters.DateFilter(
        field_name="planned_date", lookup_expr="lte"
    )
    planned_date_range = django_filters.DateRangeFilter(field_name="planned_date")

    # Фильтры по времени
    planned_departure_time__gte = django_filters.TimeFilter(
        field_name="planned_departure_time", lookup_expr="gte"
    )
    planned_departure_time__lte = django_filters.TimeFilter(
        field_name="planned_departure_time", lookup_expr="lte"
    )

    # Фильтры по высоте
    min_altitude__gte = django_filters.NumberFilter(
        field_name="min_altitude", lookup_expr="gte"
    )
    min_altitude__lte = django_filters.NumberFilter(
        field_name="min_altitude", lookup_expr="lte"
    )
    max_altitude__gte = django_filters.NumberFilter(
        field_name="max_altitude", lookup_expr="gte"
    )
    max_altitude__lte = django_filters.NumberFilter(
        field_name="max_altitude", lookup_expr="lte"
    )

    # Фильтры по связанным объектам
    operator = django_filters.UUIDFilter(field_name="operator__id")
    operator_name = django_filters.CharFilter(
        field_name="operator__name", lookup_expr="icontains"
    )
    organization_type = django_filters.CharFilter(
        field_name="operator__organization_type", lookup_expr="icontains"
    )

    drone_type = django_filters.UUIDFilter(field_name="drone_type__id")
    drone_type_code = django_filters.CharFilter(field_name="drone_type__code")

    flight_zone = django_filters.UUIDFilter(field_name="flight_zone__id")
    flight_zone_code = django_filters.CharFilter(field_name="flight_zone__code")

    departure_region = django_filters.UUIDFilter(field_name="departure_region__id")
    departure_region_name = django_filters.CharFilter(
        field_name="departure_region__name", lookup_expr="icontains"
    )

    destination_region = django_filters.UUIDFilter(field_name="destination_region__id")
    destination_region_name = django_filters.CharFilter(
        field_name="destination_region__name", lookup_expr="icontains"
    )

    # Фильтр по наличию фактических данных
    has_actual_flight = django_filters.BooleanFilter(method="filter_has_actual_flight")

    # Геопространственные фильтры
    near_point = django_filters.CharFilter(method="filter_near_point")
    within_radius = django_filters.NumberFilter(method="filter_within_radius")

    # Фильтры по тексту
    purpose = django_filters.CharFilter(field_name="purpose", lookup_expr="icontains")
    flight_id = django_filters.CharFilter(
        field_name="flight_id", lookup_expr="icontains"
    )
    sid = django_filters.CharFilter(field_name="sid", lookup_expr="icontains")
    reg_number = django_filters.CharFilter(
        field_name="reg_number", lookup_expr="icontains"
    )

    class Meta:
        model = FlightPlan
        fields = [
            "planned_date",
            "operator",
            "drone_type",
            "flight_zone",
            "departure_region",
            "destination_region",
        ]

    def filter_has_actual_flight(self, queryset, name, value):
        """Фильтр по наличию фактических данных полета."""
        if value is True:
            return queryset.filter(actualflight__isnull=False)
        elif value is False:
            return queryset.filter(actualflight__isnull=True)
        return queryset

    def filter_near_point(self, queryset, name, value):
        """Фильтр по близости к точке (формат: lat,lon)."""
        try:
            lat, lon = map(float, value.split(","))
            point = Point(lon, lat)
            self.base_filters["_point"] = point
            return queryset
        except (ValueError, TypeError):
            return queryset

    def filter_within_radius(self, queryset, name, value):
        """Фильтр по радиусу от точки (в метрах)."""
        point = getattr(self.base_filters, "_point", None)
        if point and value:
            try:
                radius = Distance(m=float(value))
                return queryset.filter(departure_point__distance_lte=(point, radius))
            except (ValueError, TypeError):
                pass
        return queryset


class ActualFlightFilter(django_filters.FilterSet):
    """Фильтры для фактических полетов."""

    # Фильтры по дате вылета
    actual_departure_date = django_filters.DateFilter()
    actual_departure_date__gte = django_filters.DateFilter(
        field_name="actual_departure_date", lookup_expr="gte"
    )
    actual_departure_date__lte = django_filters.DateFilter(
        field_name="actual_departure_date", lookup_expr="lte"
    )
    actual_departure_date_range = django_filters.DateRangeFilter(
        field_name="actual_departure_date"
    )

    # Фильтры по дате прибытия
    actual_arrival_date = django_filters.DateFilter()
    actual_arrival_date__gte = django_filters.DateFilter(
        field_name="actual_arrival_date", lookup_expr="gte"
    )
    actual_arrival_date__lte = django_filters.DateFilter(
        field_name="actual_arrival_date", lookup_expr="lte"
    )

    # Фильтры по времени
    actual_departure_time__gte = django_filters.TimeFilter(
        field_name="actual_departure_time", lookup_expr="gte"
    )
    actual_departure_time__lte = django_filters.TimeFilter(
        field_name="actual_departure_time", lookup_expr="lte"
    )

    actual_arrival_time__gte = django_filters.TimeFilter(
        field_name="actual_arrival_time", lookup_expr="gte"
    )
    actual_arrival_time__lte = django_filters.TimeFilter(
        field_name="actual_arrival_time", lookup_expr="lte"
    )

    # Фильтр по статусу полета
    flight_status = django_filters.ChoiceFilter(
        choices=ActualFlight.flight_status.field.choices
    )

    # Фильтры по продолжительности
    duration_minutes__gte = django_filters.NumberFilter(method="filter_duration_gte")
    duration_minutes__lte = django_filters.NumberFilter(method="filter_duration_lte")

    # Фильтры по связанному плану полета
    flight_plan_id = django_filters.CharFilter(field_name="flight_plan__flight_id")
    operator_name = django_filters.CharFilter(
        field_name="flight_plan__operator__name", lookup_expr="icontains"
    )
    drone_type_code = django_filters.CharFilter(
        field_name="flight_plan__drone_type__code"
    )

    # Фильтры по регионам
    departure_region = django_filters.UUIDFilter(
        field_name="flight_plan__departure_region__id"
    )
    departure_region_name = django_filters.CharFilter(
        field_name="flight_plan__departure_region__name", lookup_expr="icontains"
    )

    class Meta:
        model = ActualFlight
        fields = ["flight_status", "actual_departure_date", "actual_arrival_date"]

    def filter_duration_gte(self, queryset, name, value):
        """Фильтр по минимальной продолжительности в минутах."""
        try:
            from datetime import timedelta

            min_duration = timedelta(minutes=int(value))
            return queryset.filter(actual_duration__gte=min_duration)
        except (ValueError, TypeError):
            return queryset

    def filter_duration_lte(self, queryset, name, value):
        """Фильтр по максимальной продолжительности в минутах."""
        try:
            from datetime import timedelta

            max_duration = timedelta(minutes=int(value))
            return queryset.filter(actual_duration__lte=max_duration)
        except (ValueError, TypeError):
            return queryset


class FlightStatisticsFilter(django_filters.FilterSet):
    """Фильтры для статистики полетов."""

    # Фильтры по дате
    date = django_filters.DateFilter()
    date__gte = django_filters.DateFilter(field_name="date", lookup_expr="gte")
    date__lte = django_filters.DateFilter(field_name="date", lookup_expr="lte")
    date_range = django_filters.DateRangeFilter(field_name="date")

    # Фильтры по региону
    region = django_filters.UUIDFilter(field_name="region__id")
    region_name = django_filters.CharFilter(
        field_name="region__name", lookup_expr="icontains"
    )
    region_code = django_filters.CharFilter(field_name="region__code")

    # Фильтры по количественным показателям
    planned_flights_count__gte = django_filters.NumberFilter(
        field_name="planned_flights_count", lookup_expr="gte"
    )
    planned_flights_count__lte = django_filters.NumberFilter(
        field_name="planned_flights_count", lookup_expr="lte"
    )

    completed_flights_count__gte = django_filters.NumberFilter(
        field_name="completed_flights_count", lookup_expr="gte"
    )
    completed_flights_count__lte = django_filters.NumberFilter(
        field_name="completed_flights_count", lookup_expr="lte"
    )

    unique_operators_count__gte = django_filters.NumberFilter(
        field_name="unique_operators_count", lookup_expr="gte"
    )
    unique_operators_count__lte = django_filters.NumberFilter(
        field_name="unique_operators_count", lookup_expr="lte"
    )

    # Фильтр по проценту выполнения
    completion_rate__gte = django_filters.NumberFilter(
        method="filter_completion_rate_gte"
    )
    completion_rate__lte = django_filters.NumberFilter(
        method="filter_completion_rate_lte"
    )

    # Фильтр по наличию полетов
    has_flights = django_filters.BooleanFilter(method="filter_has_flights")

    class Meta:
        model = FlightStatistics
        fields = ["date", "region"]

    def filter_completion_rate_gte(self, queryset, name, value):
        """Фильтр по минимальному проценту выполнения."""
        try:
            from django.db.models import Case, FloatField, When

            rate = float(value)
            return queryset.annotate(
                completion_rate=Case(
                    When(planned_flights_count=0, then=0.0),
                    default=(
                        100.0
                        * models.F("completed_flights_count")
                        / models.F("planned_flights_count")
                    ),
                    output_field=FloatField(),
                )
            ).filter(completion_rate__gte=rate)
        except (ValueError, TypeError):
            return queryset

    def filter_completion_rate_lte(self, queryset, name, value):
        """Фильтр по максимальному проценту выполнения."""
        try:
            from django.db.models import Case, FloatField, When

            rate = float(value)
            return queryset.annotate(
                completion_rate=Case(
                    When(planned_flights_count=0, then=0.0),
                    default=(
                        100.0
                        * models.F("completed_flights_count")
                        / models.F("planned_flights_count")
                    ),
                    output_field=FloatField(),
                )
            ).filter(completion_rate__lte=rate)
        except (ValueError, TypeError):
            return queryset

    def filter_has_flights(self, queryset, name, value):
        """Фильтр по наличию полетов."""
        if value is True:
            return queryset.filter(planned_flights_count__gt=0)
        elif value is False:
            return queryset.filter(planned_flights_count=0)
        return queryset


class RegionFlightFilter(django_filters.FilterSet):
    """Специальный фильтр для полетов по регионам."""

    region_codes = django_filters.BaseInFilter(
        field_name="departure_region__code", lookup_expr="in"
    )

    exclude_regions = django_filters.BaseInFilter(
        field_name="departure_region__code", lookup_expr="in", exclude=True
    )

    min_flights_per_region = django_filters.NumberFilter(
        method="filter_min_flights_per_region"
    )

    class Meta:
        model = FlightPlan
        fields = []

    def filter_min_flights_per_region(self, queryset, name, value):
        """Фильтр регионов с минимальным количеством полетов."""
        try:
            from django.db.models import Count

            min_count = int(value)
            # Получаем регионы с достаточным количеством полетов
            regions_with_enough_flights = (
                queryset.values("departure_region")
                .annotate(flights_count=Count("id"))
                .filter(flights_count__gte=min_count)
                .values_list("departure_region", flat=True)
            )

            return queryset.filter(departure_region__in=regions_with_enough_flights)
        except (ValueError, TypeError):
            return queryset


class OperatorFlightFilter(django_filters.FilterSet):
    """Специальный фильтр для полетов по операторам."""

    organization_types = django_filters.BaseInFilter(
        field_name="operator__organization_type", lookup_expr="in"
    )

    exclude_organization_types = django_filters.BaseInFilter(
        field_name="operator__organization_type", lookup_expr="in", exclude=True
    )

    min_flights_per_operator = django_filters.NumberFilter(
        method="filter_min_flights_per_operator"
    )

    operator_phone_exists = django_filters.BooleanFilter(
        method="filter_operator_phone_exists"
    )

    class Meta:
        model = FlightPlan
        fields = []

    def filter_min_flights_per_operator(self, queryset, name, value):
        """Фильтр операторов с минимальным количеством полетов."""
        try:
            from django.db.models import Count

            min_count = int(value)
            operators_with_enough_flights = (
                queryset.values("operator")
                .annotate(flights_count=Count("id"))
                .filter(flights_count__gte=min_count)
                .values_list("operator", flat=True)
            )

            return queryset.filter(operator__in=operators_with_enough_flights)
        except (ValueError, TypeError):
            return queryset

    def filter_operator_phone_exists(self, queryset, name, value):
        """Фильтр по наличию телефона у оператора."""
        if value is True:
            return queryset.exclude(operator__phone__exact="")
        elif value is False:
            return queryset.filter(operator__phone__exact="")
        return queryset
