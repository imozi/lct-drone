"""
Сериализаторы для API приложения flights.
"""

from django.contrib.gis.geos import Point
from rest_framework import serializers
from rest_framework_gis.serializers import GeoFeatureModelSerializer

from .models import (
    ActualFlight,
    DroneOperator,
    DroneType,
    FlightPlan,
    FlightStatistics,
    FlightZone,
    RussianRegion,
)


class RussianRegionSerializer(serializers.ModelSerializer):
    """Сериализатор для регионов РФ с геометрией в нужном формате."""

    class Meta:
        model = RussianRegion
        fields = ["id", "name", "code", "okato", "status", "utc", "timezone", "area"]


class RussianRegionListSerializer(serializers.ModelSerializer):
    """Упрощенный сериализатор для списка регионов без геометрии."""

    class Meta:
        model = RussianRegion
        fields = ["id", "name", "code"]


class DroneOperatorSerializer(serializers.ModelSerializer):
    """Сериализатор для операторов БАС."""

    flights_count = serializers.IntegerField(read_only=True)

    class Meta:
        model = DroneOperator
        fields = [
            "id",
            "name",
            "phone",
            "organization_type",
            "created",
            "modified",
            "flights_count",
        ]


class DroneTypeSerializer(serializers.ModelSerializer):
    """Сериализатор для типов БАС."""

    flights_count = serializers.IntegerField(read_only=True)

    class Meta:
        model = DroneType
        fields = [
            "id",
            "code",
            "name",
            "description",
            "created",
            "modified",
            "flights_count",
        ]


class FlightZoneSerializer(GeoFeatureModelSerializer):
    """Сериализатор для зон полетов."""

    flights_count = serializers.IntegerField(read_only=True)

    class Meta:
        model = FlightZone
        geo_field = "geometry"
        fields = ["id", "code", "name", "created", "modified", "flights_count"]


class FlightPlanSerializer(serializers.ModelSerializer):
    """Сериализатор для планов полетов."""

    operator_name = serializers.CharField(source="operator.name", read_only=True)
    departure_point_wkt = serializers.SerializerMethodField(help_text="Точка вылета в формате WKT")
    destination_point_wkt = serializers.SerializerMethodField(help_text="Точка назначения в формате WKT")
    drone_type_code = serializers.CharField(source="drone_type.code", read_only=True)
    departure_region_name = serializers.CharField(
        source="departure_region.name", read_only=True
    )
    destination_region_name = serializers.CharField(
        source="destination_region.name", read_only=True
    )
    flight_zone_code = serializers.CharField(source="flight_zone.code", read_only=True)

    departure_latitude = serializers.SerializerMethodField()
    departure_longitude = serializers.SerializerMethodField()
    destination_latitude = serializers.SerializerMethodField()
    destination_longitude = serializers.SerializerMethodField()

    has_actual_flight = serializers.SerializerMethodField()

    class Meta:
        model = FlightPlan
        fields = [
            "id",
            "flight_id",
            "sid",
            "reg_number",
            "planned_date",
            "planned_departure_time",
            "planned_duration",
            "min_altitude",
            "max_altitude",
            "departure_point_wkt",
            "destination_point_wkt",
            "departure_latitude",
            "departure_longitude",
            "destination_latitude",
            "destination_longitude",
            "operator",
            "operator_name",
            "drone_type",
            "drone_type_code",
            "flight_zone",
            "flight_zone_code",
            "departure_region",
            "departure_region_name",
            "destination_region",
            "destination_region_name",
            "purpose",
            "special_conditions",
            "has_actual_flight",
            "created",
            "modified",
        ]

    def get_departure_latitude(self, obj) -> float:
        """Получение широты точки вылета."""
        return obj.departure_point.y if obj.departure_point else None

    def get_departure_longitude(self, obj) -> float:
        """Получение долготы точки вылета."""
        return obj.departure_point.x if obj.departure_point else None

    def get_destination_latitude(self, obj) -> float:
        """Получение широты точки назначения."""
        return obj.destination_point.y if obj.destination_point else None

    def get_destination_longitude(self, obj) -> float:
        """Получение долготы точки назначения."""
        return obj.destination_point.x if obj.destination_point else None

    def get_departure_point_wkt(self, obj) -> str:
        """Получение точки вылета в формате WKT."""
        return str(obj.departure_point) if obj.departure_point else None

    def get_destination_point_wkt(self, obj) -> str:
        """Получение точки назначения в формате WKT."""
        return str(obj.destination_point) if obj.destination_point else None

    def get_has_actual_flight(self, obj) -> bool:
        """Проверка наличия фактических данных полета."""
        return hasattr(obj, "actualflight")


class FlightPlanGeoSerializer(GeoFeatureModelSerializer):
    """GeoJSON сериализатор для планов полетов."""

    operator_name = serializers.CharField(source="operator.name", read_only=True)
    departure_point_wkt = serializers.SerializerMethodField(help_text="Точка вылета в формате WKT")
    destination_point_wkt = serializers.SerializerMethodField(help_text="Точка назначения в формате WKT")
    drone_type_code = serializers.CharField(source="drone_type.code", read_only=True)

    class Meta:
        model = FlightPlan
        geo_field = "departure_point"
        fields = [
            "id",
            "flight_id",
            "planned_date",
            "planned_departure_time",
            "operator_name",
            "drone_type_code",
            "departure_point_wkt",
            "destination_point_wkt",
            "purpose",
        ]

    def get_departure_point_wkt(self, obj) -> str:
        """Получение точки вылета в формате WKT."""
        return str(obj.departure_point) if obj.departure_point else None

    def get_destination_point_wkt(self, obj) -> str:
        """Получение точки назначения в формате WKT."""
        return str(obj.destination_point) if obj.destination_point else None


class ActualFlightSerializer(serializers.ModelSerializer):
    """Сериализатор для фактических полетов."""

    flight_plan_id = serializers.CharField(
        source="flight_plan.flight_id", read_only=True
    )
    operator_name = serializers.CharField(
        source="flight_plan.operator.name", read_only=True
    )

    actual_departure_latitude = serializers.SerializerMethodField()
    actual_departure_longitude = serializers.SerializerMethodField()
    actual_destination_latitude = serializers.SerializerMethodField()
    actual_destination_longitude = serializers.SerializerMethodField()

    duration_minutes = serializers.SerializerMethodField()

    class Meta:
        model = ActualFlight
        fields = [
            "id",
            "flight_plan",
            "flight_plan_id",
            "operator_name",
            "actual_departure_date",
            "actual_departure_time",
            "actual_arrival_date",
            "actual_arrival_time",
            "actual_departure_point",
            "actual_destination_point",
            "actual_departure_latitude",
            "actual_departure_longitude",
            "actual_destination_latitude",
            "actual_destination_longitude",
            "actual_duration",
            "duration_minutes",
            "flight_status",
            "created",
            "modified",
        ]

    def get_actual_departure_latitude(self, obj) -> float:
        """Получение широты фактической точки вылета."""
        return obj.actual_departure_point.y if obj.actual_departure_point else None

    def get_actual_departure_longitude(self, obj) -> float:
        """Получение долготы фактической точки вылета."""
        return obj.actual_departure_point.x if obj.actual_departure_point else None

    def get_actual_destination_latitude(self, obj) -> float:
        """Получение широты фактической точки назначения."""
        return obj.actual_destination_point.y if obj.actual_destination_point else None

    def get_actual_destination_longitude(self, obj) -> float:
        """Получение долготы фактической точки назначения."""
        return obj.actual_destination_point.x if obj.actual_destination_point else None

    def get_duration_minutes(self, obj) -> int:
        """Получение продолжительности полета в минутах."""
        if obj.actual_duration:
            return int(obj.actual_duration.total_seconds() / 60)
        return None


class FlightStatisticsSerializer(serializers.ModelSerializer):
    """Сериализатор для статистики полетов."""

    region_name = serializers.CharField(source="region.name", read_only=True)
    region_code = serializers.CharField(source="region.code", read_only=True)

    total_flight_time_hours = serializers.SerializerMethodField()
    completion_rate = serializers.SerializerMethodField()

    class Meta:
        model = FlightStatistics
        fields = [
            "id",
            "region",
            "region_name",
            "region_code",
            "date",
            "planned_flights_count",
            "completed_flights_count",
            "total_flight_time",
            "total_flight_time_hours",
            "unique_operators_count",
            "completion_rate",
            "created",
            "modified",
        ]

    def get_total_flight_time_hours(self, obj) -> float:
        """Получение общего времени полетов в часах."""
        if obj.total_flight_time:
            return round(obj.total_flight_time.total_seconds() / 3600, 2)
        return 0.0

    def get_completion_rate(self, obj) -> float:
        """Расчет процента выполненных полетов."""
        if obj.planned_flights_count > 0:
            return round(
                (obj.completed_flights_count / obj.planned_flights_count) * 100, 1
            )
        return 0.0


class RegionalSummarySerializer(serializers.Serializer):
    """Сериализатор для сводки по регионам."""

    region_name = serializers.CharField()
    region_code = serializers.CharField()
    total_planned = serializers.IntegerField()
    total_completed = serializers.IntegerField()
    total_operators = serializers.IntegerField()
    completion_rate = serializers.SerializerMethodField()

    def get_completion_rate(self, obj) -> float:
        """Расчет процента выполненных полетов."""
        if obj["total_planned"] and obj["total_planned"] > 0:
            return round((obj["total_completed"] / obj["total_planned"]) * 100, 1)
        return 0.0


class OperatorStatisticsSerializer(serializers.Serializer):
    """Сериализатор для статистики операторов."""

    operator_name = serializers.CharField(source="operator__name")
    organization_type = serializers.CharField(source="operator__organization_type")
    planned_flights = serializers.IntegerField()
    completed_flights = serializers.IntegerField()
    avg_duration_minutes = serializers.SerializerMethodField()
    completion_rate = serializers.SerializerMethodField()

    def get_avg_duration_minutes(self, obj) -> int:
        """Получение средней продолжительности в минутах."""
        if obj.get("avg_duration"):
            return int(obj["avg_duration"].total_seconds() / 60)
        return 0

    def get_completion_rate(self, obj) -> float:
        """Расчет процента выполненных полетов."""
        planned = obj.get("planned_flights", 0)
        completed = obj.get("completed_flights", 0)
        if planned > 0:
            return round((completed / planned) * 100, 1)
        return 0.0


class FlightCreateSerializer(serializers.ModelSerializer):
    """Сериализатор для создания планов полетов через API."""

    departure_latitude = serializers.FloatField(write_only=True)
    departure_longitude = serializers.FloatField(write_only=True)
    destination_latitude = serializers.FloatField(write_only=True)
    destination_longitude = serializers.FloatField(write_only=True)

    class Meta:
        model = FlightPlan
        fields = [
            "flight_id",
            "sid",
            "reg_number",
            "planned_date",
            "planned_departure_time",
            "planned_duration",
            "min_altitude",
            "max_altitude",
            "departure_latitude",
            "departure_longitude",
            "destination_latitude",
            "destination_longitude",
            "operator",
            "drone_type",
            "flight_zone",
            "purpose",
            "special_conditions",
        ]

    def create(self, validated_data):
        """Создание плана полета с координатами."""
        dep_lat = validated_data.pop("departure_latitude")
        dep_lon = validated_data.pop("departure_longitude")
        dest_lat = validated_data.pop("destination_latitude")
        dest_lon = validated_data.pop("destination_longitude")

        validated_data["departure_point"] = Point(dep_lon, dep_lat)
        validated_data["destination_point"] = Point(dest_lon, dest_lat)

        return super().create(validated_data)


class FileUploadSerializer(serializers.Serializer):
    """Сериализатор для загрузки файлов через API."""

    excel_file = serializers.FileField()

    def validate_excel_file(self, value):
        """Валидация Excel файла."""
        if not value.name.endswith((".xlsx", ".xls")):
            raise serializers.ValidationError(
                "Неподдерживаемый формат файла. Разрешены только .xlsx и .xls"
            )

        if value.size > 52428800:  # 50MB
            raise serializers.ValidationError("Размер файла не должен превышать 50MB")

        return value


class ReportParametersSerializer(serializers.Serializer):
    """Сериализатор для параметров отчетов."""

    REPORT_TYPES = [
        ("daily", "Ежедневный"),
        ("weekly", "Еженедельный"),
        ("monthly", "Месячный"),
        ("regional", "По регионам"),
        ("operator", "По операторам"),
    ]

    FORMATS = [
        ("json", "JSON"),
        ("csv", "CSV"),
        ("xlsx", "Excel"),
        ("png", "График PNG"),
    ]

    report_type = serializers.ChoiceField(choices=REPORT_TYPES)
    start_date = serializers.DateField()
    end_date = serializers.DateField()
    regions = serializers.ListField(
        child=serializers.UUIDField(), required=False, allow_empty=True
    )
    format = serializers.ChoiceField(choices=FORMATS, default="json")
    include_charts = serializers.BooleanField(default=False)

    def validate(self, data):
        """Валидация параметров отчета."""
        if data["start_date"] > data["end_date"]:
            raise serializers.ValidationError(
                "Дата начала не может быть позже даты окончания"
            )

        from datetime import timedelta

        if (data["end_date"] - data["start_date"]) > timedelta(days=365):
            raise serializers.ValidationError("Максимальный период для отчета - 1 год")

        return data


class StatisticsResponseSerializer(serializers.Serializer):
    """Базовый сериализатор для статистических ответов."""

    def to_representation(self, instance):
        # Возвращаем данные как есть для совместимости с существующим API
        return instance


class DashboardStatisticsSerializer(StatisticsResponseSerializer):
    """Сериализатор для ответа дашборда статистики."""

    class Meta:
        # Этот класс используется только для документации OpenAPI
        pass


class RegionalAnnualStatisticsSerializer(StatisticsResponseSerializer):
    """Сериализатор для ответа региональной годовой статистики."""

    class Meta:
        # Этот класс используется только для документации OpenAPI
        pass
