"""
Комплексные API ViewSets для работы с полетными данными.
"""

import logging
import statistics
import time
from datetime import date, datetime, timedelta
from typing import Any, Dict

from django.db.models import Avg, Count, F, Q, Sum
from django.db.models.functions import TruncMonth
from django.http import HttpResponse
from django.utils import timezone
from django_filters.rest_framework import DjangoFilterBackend
from drf_spectacular.utils import OpenApiParameter, extend_schema
from drf_spectacular.types import OpenApiTypes
from rest_framework import filters, permissions, status, viewsets
from rest_framework.decorators import action
from rest_framework.parsers import FormParser, MultiPartParser
from rest_framework.response import Response

from .analytics_services import AdvancedAnalyticsService
from .filters import FlightPlanFilter
from .models import (
    DroneOperator,
    DroneType,
    FlightPlan,
    RussianRegion,
)
from .serializers import (
    DashboardStatisticsSerializer,
    DroneOperatorSerializer,
    DroneTypeSerializer,
    FileUploadSerializer,
    FlightCreateSerializer,
    FlightPlanGeoSerializer,
    FlightPlanSerializer,
    OperatorStatisticsSerializer,
    RegionalAnnualStatisticsSerializer,
    RussianRegionSerializer,
    StatisticsResponseSerializer,
)
from .services import FlightDataParser

logger = logging.getLogger(__name__)


@extend_schema(tags=["Полетные планы"])
class FlightPlanViewSet(viewsets.ReadOnlyModelViewSet):
    """
    ViewSet для работы с планами полетов.

    Предоставляет операции чтения и дополнительные эндпоинты для:
    - Загрузки Excel файлов
    - Получения данных для карты
    - Статистики
    """

    queryset = FlightPlan.objects.select_related(
        "operator",
        "drone_type",
        "flight_zone",
        "departure_region",
        "destination_region",
    ).prefetch_related("actualflight")

    serializer_class = FlightPlanSerializer
    permission_classes = [permissions.IsAuthenticatedOrReadOnly]

    filter_backends = [
        DjangoFilterBackend,
        filters.SearchFilter,
        filters.OrderingFilter,
    ]
    filterset_class = FlightPlanFilter
    search_fields = ["flight_id", "sid", "reg_number", "operator__name"]
    ordering_fields = ["planned_date", "planned_departure_time", "created"]
    ordering = ["-planned_date", "-planned_departure_time"]

    def get_serializer_class(self):
        """Выбор сериализатора в зависимости от действия."""
        if self.action == "create":
            return FlightCreateSerializer
        elif self.action == "map_data":
            return FlightPlanGeoSerializer
        return FlightPlanSerializer

    @extend_schema(
        summary="Загрузка планов полетов из Excel файла",
    )
    @action(
        detail=False, methods=["post"], parser_classes=[MultiPartParser, FormParser]
    )
    def upload_excel(self, request) -> Response:
        """
        Загрузка планов полетов из Excel файла.

        POST /api/flight-plans/upload_excel/

        Принимает:
        - excel_file: Excel файл (.xlsx, .xls)

        Возвращает:
        - success: статус загрузки
        - message: сообщение об успехе/ошибке
        - loading_time_minutes: время затраченное на загрузку в минутах
        - total_flight_plans: общее количество полетных планов
        - successfully_loaded: количество успешно загруженных
        - validation_failures: количество не прошедших валидацию
        - loading_status: статус завершения загрузки
        """
        if not request.user.is_staff:
            return Response(
                {"error": "Недостаточно прав для загрузки файлов"},
                status=status.HTTP_403_FORBIDDEN,
            )

        serializer = FileUploadSerializer(data=request.data)
        if not serializer.is_valid():
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

        excel_file = serializer.validated_data["excel_file"]

        start_time = time.time()

        try:
            parser = FlightDataParser()
            result = parser.parse_excel_file(excel_file)

            end_time = time.time()
            loading_time_seconds = end_time - start_time
            loading_time_minutes = round(loading_time_seconds / 60, 2)

            total_flight_plans = result["processed"]
            successfully_loaded = result["created"]
            validation_failures = result["errors"]
            loading_status = "завершено"

            return Response(
                {
                    "success": True,
                    "message": "Файл обработан успешно",
                    "loading_time_minutes": loading_time_minutes,
                    "total_flight_plans": total_flight_plans,
                    "successfully_loaded": successfully_loaded,
                    "validation_failures": validation_failures,
                    "loading_status": loading_status,
                },
                status=status.HTTP_201_CREATED,
            )

        except Exception as e:
            end_time = time.time()
            loading_time_seconds = end_time - start_time
            loading_time_minutes = round(loading_time_seconds / 60, 2)

            logger.error(f"Ошибка загрузки Excel файла: {e}")
            return Response(
                {
                    "success": False,
                    "error": f"Ошибка обработки файла: {str(e)}",
                    "loading_time_minutes": loading_time_minutes,
                    "total_flight_plans": 0,
                    "successfully_loaded": 0,
                    "validation_failures": 0,
                    "loading_status": "ошибка",
                },
                status=status.HTTP_500_INTERNAL_SERVER_ERROR,
            )

    @extend_schema(exclude=True)
    @action(detail=False, methods=["get"])
    def map_data(self, request) -> Response:
        """
        Получение данных планов полетов в формате GeoJSON для отображения на карте.

        GET /api/flight-plans/map_data/

        Query параметры:
        - date_from: дата начала (YYYY-MM-DD)
        - date_to: дата окончания (YYYY-MM-DD)
        - region: код региона
        - status: статус полета (planned, departed, completed)

        Возвращает GeoJSON FeatureCollection.
        """
        queryset = self.filter_queryset(self.get_queryset())

        date_from = request.query_params.get("date_from")
        date_to = request.query_params.get("date_to")
        region_code = request.query_params.get("region")
        flight_status = request.query_params.get("status")

        if date_from:
            try:
                date_from = datetime.strptime(date_from, "%Y-%m-%d").date()
                queryset = queryset.filter(planned_date__gte=date_from)
            except ValueError:
                pass

        if date_to:
            try:
                date_to = datetime.strptime(date_to, "%Y-%m-%d").date()
                queryset = queryset.filter(planned_date__lte=date_to)
            except ValueError:
                pass

        if region_code:
            queryset = queryset.filter(
                Q(departure_region__code=region_code)
                | Q(destination_region__code=region_code)
            )

        if flight_status:
            if flight_status == "planned":
                queryset = queryset.filter(actualflight__isnull=True)
            else:
                queryset = queryset.filter(actualflight__flight_status=flight_status)

        queryset = queryset[:1000]

        serializer = FlightPlanGeoSerializer(queryset, many=True)
        return Response(
            {
                "type": "FeatureCollection",
                "features": serializer.data,
                "count": len(serializer.data),
            }
        )

    @extend_schema(exclude=True)
    @action(detail=False, methods=["get"])
    def time_statistics(self, request) -> Response:
        """
        Статистика полетов по времени.

        GET /api/flight-plans/time_statistics/

        Query параметры:
        - period: day, week, month, year (по умолчанию month)
        - date_from: дата начала
        - date_to: дата окончания
        """
        period = request.query_params.get("period", "month")
        date_from = request.query_params.get("date_from")
        date_to = request.query_params.get("date_to")

        try:
            if date_from:
                date_from = datetime.strptime(date_from, "%Y-%m-%d").date()
            else:
                date_from = date.today() - timedelta(days=90)

            if date_to:
                date_to = datetime.strptime(date_to, "%Y-%m-%d").date()
            else:
                date_to = date.today()
        except ValueError:
            return Response(
                {"error": "Неверный формат даты. Используйте YYYY-MM-DD"},
                status=status.HTTP_400_BAD_REQUEST,
            )

        queryset = FlightPlan.objects.filter(planned_date__range=[date_from, date_to])

        if period == "day":
            time_stats = (
                queryset.extra(select={"period": "DATE(planned_date)"})
                .values("period")
                .annotate(
                    flights_count=Count("id"),
                    completed_count=Count(
                        "actualflight",
                        filter=Q(actualflight__flight_status="completed"),
                    ),
                    avg_duration=Avg("planned_duration"),
                    operators_count=Count("operator", distinct=True),
                )
                .order_by("period")
            )

        elif period == "week":
            time_stats = (
                queryset.extra(select={"period": "DATE_TRUNC('week', planned_date)"})
                .values("period")
                .annotate(
                    flights_count=Count("id"),
                    completed_count=Count(
                        "actualflight",
                        filter=Q(actualflight__flight_status="completed"),
                    ),
                    avg_duration=Avg("planned_duration"),
                    operators_count=Count("operator", distinct=True),
                )
                .order_by("period")
            )

        elif period == "month":
            time_stats = (
                queryset.extra(select={"period": "DATE_TRUNC('month', planned_date)"})
                .values("period")
                .annotate(
                    flights_count=Count("id"),
                    completed_count=Count(
                        "actualflight",
                        filter=Q(actualflight__flight_status="completed"),
                    ),
                    avg_duration=Avg("planned_duration"),
                    operators_count=Count("operator", distinct=True),
                )
                .order_by("period")
            )

        else:
            time_stats = (
                queryset.extra(select={"period": "DATE_TRUNC('year', planned_date)"})
                .values("period")
                .annotate(
                    flights_count=Count("id"),
                    completed_count=Count(
                        "actualflight",
                        filter=Q(actualflight__flight_status="completed"),
                    ),
                    avg_duration=Avg("planned_duration"),
                    operators_count=Count("operator", distinct=True),
                )
                .order_by("period")
            )

        formatted_stats = []
        for stat in time_stats:
            formatted_stats.append(
                {
                    "period": stat["period"],
                    "flights_count": stat["flights_count"],
                    "completed_count": stat["completed_count"] or 0,
                    "completion_rate": (
                        round(
                            (stat["completed_count"] or 0)
                            / stat["flights_count"]
                            * 100,
                            1,
                        )
                        if stat["flights_count"] > 0
                        else 0
                    ),
                    "avg_duration_minutes": (
                        int(stat["avg_duration"].total_seconds() / 60)
                        if stat["avg_duration"]
                        else 0
                    ),
                    "operators_count": stat["operators_count"],
                }
            )

        return Response(
            {
                "period_type": period,
                "date_range": {
                    "from": date_from.isoformat(),
                    "to": date_to.isoformat(),
                },
                "statistics": formatted_stats,
                "summary": {
                    "total_flights": sum(s["flights_count"] for s in formatted_stats),
                    "total_completed": sum(
                        s["completed_count"] for s in formatted_stats
                    ),
                    "overall_completion_rate": round(
                        sum(s["completed_count"] for s in formatted_stats)
                        / max(sum(s["flights_count"] for s in formatted_stats), 1)
                        * 100,
                        1,
                    ),
                },
            }
        )

    @extend_schema(exclude=True)
    @action(detail=False, methods=["get"])
    def regional_statistics(self, request) -> Response:
        """
        Расширенная статистика по регионам.

        GET /api/flight-plans/regional_statistics/
        """
        date_from = request.query_params.get("date_from")
        date_to = request.query_params.get("date_to")

        try:
            if date_from:
                date_from = datetime.strptime(date_from, "%Y-%m-%d").date()
            else:
                date_from = date.today() - timedelta(days=30)

            if date_to:
                date_to = datetime.strptime(date_to, "%Y-%m-%d").date()
            else:
                date_to = date.today()
        except ValueError:
            return Response(
                {"error": "Неверный формат даты"}, status=status.HTTP_400_BAD_REQUEST
            )

        departure_stats = (
            FlightPlan.objects.filter(
                planned_date__range=[date_from, date_to], departure_region__isnull=False
            )
            .values(
                "departure_region__id",
                "departure_region__name",
                "departure_region__code",
            )
            .annotate(
                flights_count=Count("id"),
                completed_count=Count(
                    "actualflight", filter=Q(actualflight__flight_status="completed")
                ),
                avg_duration=Avg("planned_duration"),
                min_altitude_avg=Avg("min_altitude"),
                max_altitude_avg=Avg("max_altitude"),
                operators_count=Count("operator", distinct=True),
                drone_types_count=Count("drone_type", distinct=True),
            )
            .order_by("-flights_count")
        )

        destination_stats = (
            FlightPlan.objects.filter(
                planned_date__range=[date_from, date_to],
                destination_region__isnull=False,
            )
            .values(
                "destination_region__id",
                "destination_region__name",
                "destination_region__code",
            )
            .annotate(
                flights_count=Count("id"),
                completed_count=Count(
                    "actualflight", filter=Q(actualflight__flight_status="completed")
                ),
            )
            .order_by("-flights_count")
        )

        cross_regional = (
            FlightPlan.objects.filter(
                planned_date__range=[date_from, date_to],
                departure_region__isnull=False,
                destination_region__isnull=False,
            )
            .exclude(departure_region=F("destination_region"))
            .values(
                "departure_region__id",
                "departure_region__name",
                "destination_region__id",
                "destination_region__name",
            )
            .annotate(flights_count=Count("id"))
            .order_by("-flights_count")[:10]
        )

        return Response(
            {
                "date_range": {
                    "from": date_from.isoformat(),
                    "to": date_to.isoformat(),
                },
                "departure_regions": [
                    {
                        "region_id": stat["departure_region__id"],
                        "region_name": stat["departure_region__name"],
                        "region_code": stat["departure_region__code"],
                        "flights_count": stat["flights_count"],
                        "completed_count": stat["completed_count"] or 0,
                        "completion_rate": (
                            round(
                                (stat["completed_count"] or 0)
                                / stat["flights_count"]
                                * 100,
                                1,
                            )
                            if stat["flights_count"] > 0
                            else 0
                        ),
                        "avg_duration_minutes": (
                            int(stat["avg_duration"].total_seconds() / 60)
                            if stat["avg_duration"]
                            else 0
                        ),
                        "avg_min_altitude": round(stat["min_altitude_avg"] or 0),
                        "avg_max_altitude": round(stat["max_altitude_avg"] or 0),
                        "operators_count": stat["operators_count"],
                        "drone_types_count": stat["drone_types_count"],
                    }
                    for stat in departure_stats
                ],
                "destination_regions": [
                    {
                        "region_id": stat["destination_region__id"],
                        "region_name": stat["destination_region__name"],
                        "region_code": stat["destination_region__code"],
                        "flights_count": stat["flights_count"],
                        "completed_count": stat["completed_count"] or 0,
                        "completion_rate": (
                            round(
                                (stat["completed_count"] or 0)
                                / stat["flights_count"]
                                * 100,
                                1,
                            )
                            if stat["flights_count"] > 0
                            else 0
                        ),
                    }
                    for stat in destination_stats
                ],
                "cross_regional_routes": [
                    {
                        "from_region_id": route["departure_region__id"],
                        "from": route["departure_region__name"],
                        "to_region_id": route["destination_region__id"],
                        "to": route["destination_region__name"],
                        "flights_count": route["flights_count"],
                    }
                    for route in cross_regional
                ],
            }
        )

    @extend_schema(exclude=True)
    @action(detail=False, methods=["get"])
    def operator_statistics(self, request) -> Response:
        """
        Статистика по операторам.

        GET /api/flight-plans/operator_statistics/
        """
        date_from = request.query_params.get("date_from")
        date_to = request.query_params.get("date_to")
        limit = int(request.query_params.get("limit", 20))

        queryset = FlightPlan.objects.all()

        if date_from:
            try:
                date_from = datetime.strptime(date_from, "%Y-%m-%d").date()
                queryset = queryset.filter(planned_date__gte=date_from)
            except ValueError:
                pass

        if date_to:
            try:
                date_to = datetime.strptime(date_to, "%Y-%m-%d").date()
                queryset = queryset.filter(planned_date__lte=date_to)
            except ValueError:
                pass

        operator_stats = (
            queryset.values("operator__name", "operator__organization_type")
            .annotate(
                planned_flights=Count("id"),
                completed_flights=Count(
                    "actualflight", filter=Q(actualflight__flight_status="completed")
                ),
                avg_duration=Avg("actualflight__actual_duration"),
                total_flight_time=Sum("actualflight__actual_duration"),
                regions_count=Count("departure_region", distinct=True),
                drone_types_count=Count("drone_type", distinct=True),
            )
            .order_by("-planned_flights")[:limit]
        )

        serializer = OperatorStatisticsSerializer(operator_stats, many=True)

        return Response(
            {
                "operators": serializer.data,
                "summary": {
                    "total_operators": queryset.values("operator").distinct().count(),
                    "most_active": serializer.data[0] if serializer.data else None,
                },
            }
        )

    @extend_schema(exclude=True)
    @action(detail=False, methods=["get"])
    def advanced_analytics(self, request) -> Response:
        """
        Расширенные метрики полетов.

        GET /api/flight-plans/advanced_analytics/

        Query параметры:
        - date_from: дата начала (YYYY-MM-DD)
        - date_to: дата окончания (YYYY-MM-DD)
        - metric: конкретная метрика (peak_load, daily_dynamics, growth_decline,
                 flight_density, daily_activity, zero_flight_days, comprehensive)
        """
        date_from = request.query_params.get("date_from")
        date_to = request.query_params.get("date_to")
        metric = request.query_params.get("metric", "comprehensive")

        try:
            if date_from:
                date_from = datetime.strptime(date_from, "%Y-%m-%d").date()
            else:
                date_from = date.today() - timedelta(days=30)

            if date_to:
                date_to = datetime.strptime(date_to, "%Y-%m-%d").date()
            else:
                date_to = date.today()
        except ValueError:
            return Response(
                {"error": "Неверный формат даты. Используйте YYYY-MM-DD"},
                status=status.HTTP_400_BAD_REQUEST,
            )

        try:
            if metric == "peak_load":
                result = AdvancedAnalyticsService.get_peak_load_statistics(
                    date_from, date_to
                )
            elif metric == "daily_dynamics":
                result = AdvancedAnalyticsService.get_daily_dynamics(date_from, date_to)
            elif metric == "growth_decline":
                result = AdvancedAnalyticsService.get_growth_decline_statistics(
                    date_to.replace(day=1)
                )
            elif metric == "flight_density":
                result = AdvancedAnalyticsService.get_flight_density_by_regions(
                    date_from, date_to
                )
            elif metric == "daily_activity":
                result = AdvancedAnalyticsService.get_daily_activity_distribution(
                    date_from, date_to
                )
            elif metric == "zero_flight_days":
                result = AdvancedAnalyticsService.get_zero_flight_days_by_regions(
                    date_from, date_to
                )
            else:
                result = AdvancedAnalyticsService.get_comprehensive_analytics(
                    date_from, date_to
                )

            return Response({"metric_type": metric, "data": result})

        except Exception as e:
            logger.error(f"Ошибка расчета расширенных метрик: {e}")
            return Response(
                {"error": f"Ошибка расчета метрик: {str(e)}"},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR,
            )

    @extend_schema(tags=["Дашборд и метрики"], summary="Анализ пиковой нагрузки")
    @action(detail=False, methods=["get"])
    def peak_load_analysis(self, request) -> Response:
        """
        Анализ пиковой нагрузки: максимальное число полетов за час.

        GET /api/flight-plans/peak_load_analysis/
        """
        date_from = request.query_params.get("date_from")
        date_to = request.query_params.get("date_to")

        try:
            if date_from:
                date_from = datetime.strptime(date_from, "%Y-%m-%d").date()
            if date_to:
                date_to = datetime.strptime(date_to, "%Y-%m-%d").date()

            result = AdvancedAnalyticsService.get_peak_load_statistics(
                date_from, date_to
            )
            return Response(result)

        except ValueError:
            return Response(
                {"error": "Неверный формат даты"}, status=status.HTTP_400_BAD_REQUEST
            )
        except Exception as e:
            return Response(
                {"error": str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )

    @extend_schema(tags=["Дашборд и метрики"],
                   summary="Анализ плотности полетов: число полетов на 1000км² по регионам", )
    @action(detail=False, methods=["get"])
    def flight_density_analysis(self, request) -> Response:
        """
        Анализ плотности полетов: число полетов на 1000км² по регионам.

        GET /api/flight-plans/flight_density_analysis/

        Query параметры:
        - top: количество топ регионов (если не указан, показывает все регионы)
        """
        date_from = request.query_params.get("date_from")
        date_to = request.query_params.get("date_to")
        top_param = request.query_params.get("top")
        top = int(top_param) if top_param else None

        try:
            if date_from:
                date_from = datetime.strptime(date_from, "%Y-%m-%d").date()
            if date_to:
                date_to = datetime.strptime(date_to, "%Y-%m-%d").date()

            result = AdvancedAnalyticsService.get_flight_density_by_regions(
                date_from, date_to
            )

            regions_to_show = result if top is None else result[:top]

            return Response(
                {
                    "total_regions": len(result),
                    "regions": regions_to_show,
                    "density_statistics": {
                        "max_density": (
                            max(r["density_per_1000km2"] for r in result)
                            if result
                            else 0
                        ),
                        "avg_density": round(
                            sum(r["density_per_1000km2"] for r in result)
                            / max(len(result), 1),
                            4,
                        ),
                        "total_flights": sum(r["flights_count"] for r in result),
                        "total_area_analyzed": sum(r["area_km2"] for r in result),
                    },
                }
            )

        except ValueError:
            return Response(
                {"error": "Неверный формат параметров"},
                status=status.HTTP_400_BAD_REQUEST,
            )
        except Exception as e:
            return Response(
                {"error": str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )

    @extend_schema(exclude=True)
    @action(detail=False, methods=["get"])
    def daily_activity_analysis(self, request) -> Response:
        """
        Анализ дневной активности: распределение полетов по часам.

        GET /api/flight-plans/daily_activity_analysis/
        """
        date_from = request.query_params.get("date_from")
        date_to = request.query_params.get("date_to")

        try:
            if date_from:
                date_from = datetime.strptime(date_from, "%Y-%m-%d").date()
            if date_to:
                date_to = datetime.strptime(date_to, "%Y-%m-%d").date()

            result = AdvancedAnalyticsService.get_daily_activity_distribution(
                date_from, date_to
            )
            return Response(result)

        except ValueError:
            return Response(
                {"error": "Неверный формат даты"}, status=status.HTTP_400_BAD_REQUEST
            )
        except Exception as e:
            return Response(
                {"error": str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )

    @extend_schema(exclude=True)
    @action(detail=False, methods=["get"])
    def regional_comparison(self, request) -> Response:
        """
        Сравнительный анализ регионов по всем метрикам.

        GET /api/flight-plans/regional_comparison/

        Query параметры:
        - regions: коды регионов через запятую (например: 77,78,50)
        """
        region_codes = request.query_params.get("regions", "").split(",")
        region_codes = [code.strip() for code in region_codes if code.strip()]

        if not region_codes:
            return Response(
                {"error": "Необходимо указать коды регионов через запятую"},
                status=status.HTTP_400_BAD_REQUEST,
            )

        date_from = request.query_params.get("date_from")
        date_to = request.query_params.get("date_to")

        try:
            if date_from:
                date_from = datetime.strptime(date_from, "%Y-%m-%d").date()
            if date_to:
                date_to = datetime.strptime(date_to, "%Y-%m-%d").date()

            result = AdvancedAnalyticsService.get_regional_comparison(
                region_codes, date_from, date_to
            )
            return Response(result)

        except ValueError:
            return Response(
                {"error": "Неверный формат параметров"},
                status=status.HTTP_400_BAD_REQUEST,
            )
        except Exception as e:
            return Response(
                {"error": str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )


@extend_schema(tags=["Дашборд и метрики"])
class StatisticsViewSet(viewsets.ViewSet):
    """Специализированный ViewSet для различной статистики полетов БАС."""

    permission_classes = [permissions.IsAuthenticatedOrReadOnly]
    serializer_class = StatisticsResponseSerializer

    def get_serializer_class(self):
        """Возвращает подходящий сериализатор для каждого действия."""
        if self.action == 'dashboard':
            return DashboardStatisticsSerializer
        elif self.action == 'regional_annual_statistics':
            return RegionalAnnualStatisticsSerializer
        return StatisticsResponseSerializer

    @extend_schema(
        operation_id="statistics_dashboard",
        summary="Дашборд со статистикой полетов БАС",
        description="Возвращает комплексную статистику полетов БАС по всем регионам РФ",
        tags=["Дашборд и метрики"]
    )
    @action(detail=False, methods=["get"])
    def dashboard(self, request) -> Response:
        """
        Оптимизированная комплексная статистика для дашборда.

        GET /api/statistics/dashboard/
        """
        from django.core.cache import cache
        from django.db import connection

        current_hour = datetime.now().hour
        cache_key = f"dashboard_statistics_v3_{current_hour // 4}"
        cached_data = cache.get(cache_key)
        if cached_data:
            return Response(cached_data)

        region_areas = {}
        try:
            areas_qs = RussianRegion.objects.values("code", "area")
            for region in areas_qs:
                if region["area"] and region["area"].strip():
                    try:
                        area_value = float(region["area"].replace(",", "."))
                        region_areas[region["code"]] = area_value
                    except (ValueError, AttributeError):
                        region_areas[region["code"]] = 1
                else:
                    region_areas[region["code"]] = 1
        except Exception:
            pass

        total_russia_area_km2 = cache.get("russia_total_area")
        if not total_russia_area_km2:
            try:
                total_russia_area_km2 = sum(
                    area for area in region_areas.values() if area > 0
                )
                if not total_russia_area_km2:
                    total_russia_area_km2 = 17098246
                cache.set("russia_total_area", total_russia_area_km2, 3600)
            except Exception:
                total_russia_area_km2 = 17098246

        base_stats = FlightPlan.objects.aggregate(
            total_flights=Count("id"),
            total_duration=Sum("planned_duration"),
            avg_duration=Avg("planned_duration"),
        )

        total_flights_count = base_stats["total_flights"]
        overall_flight_density = (
            (total_flights_count / total_russia_area_km2) * 1000
            if total_russia_area_km2 > 0
            else 0
        )

        total_duration_hours = 0
        avg_duration_minutes = 0
        if base_stats["total_duration"]:
            total_duration_hours = base_stats["total_duration"].total_seconds() / 3600
        if base_stats["avg_duration"]:
            avg_duration_minutes = base_stats["avg_duration"].total_seconds() / 60

        median_duration_minutes = 0
        try:

            with connection.cursor() as cursor:
                cursor.execute(
                    """
                    SELECT EXTRACT(EPOCH FROM planned_duration) / 60 as duration_minutes
                    FROM flights_flightplan
                    WHERE planned_duration IS NOT NULL
                    ORDER BY planned_duration
                    LIMIT 1 OFFSET (SELECT COUNT(*) / 2
                                    FROM flights_flightplan
                                    WHERE planned_duration IS NOT NULL)
                    """
                )
                result = cursor.fetchone()
                if result:
                    median_duration_minutes = result[0]
        except Exception:
            pass

        monthly_stats = (
            FlightPlan.objects.filter(
                planned_date__gte=date.today().replace(day=1) - timedelta(days=365)
            )
            .annotate(month=TruncMonth("planned_date"))
            .values("month")
            .annotate(
                flights_count=Count("id"),
                total_duration=Sum("planned_duration"),
                avg_duration=Avg("planned_duration"),
            )
            .order_by("month")
        )

        monthly_data = []
        for month_stat in monthly_stats:
            month_total_hours = 0
            month_avg_minutes = 0
            if month_stat["total_duration"]:
                month_total_hours = month_stat["total_duration"].total_seconds() / 3600
            if month_stat["avg_duration"]:
                month_avg_minutes = month_stat["avg_duration"].total_seconds() / 60

            month_density = (
                (month_stat["flights_count"] / total_russia_area_km2) * 1000
                if total_russia_area_km2 > 0
                else 0
            )

            month_median_minutes = 0
            try:
                with connection.cursor() as cursor:
                    cursor.execute(
                        """
                        SELECT EXTRACT(EPOCH FROM planned_duration) / 60 as duration_minutes
                        FROM flights_flightplan
                        WHERE planned_duration IS NOT NULL
                          AND DATE_TRUNC('month', planned_date) = %s
                        ORDER BY planned_duration
                        LIMIT 1 OFFSET (SELECT COUNT(*) / 2
                                        FROM flights_flightplan
                                        WHERE planned_duration IS NOT NULL
                                          AND DATE_TRUNC('month', planned_date) = %s)
                        """,
                        [month_stat["month"], month_stat["month"]],
                    )
                    result = cursor.fetchone()
                    if result:
                        month_median_minutes = result[0]
            except Exception:
                pass

            month_obj = month_stat["month"]
            if month_obj.month == 12:
                next_month = month_obj.replace(year=month_obj.year + 1, month=1)
            else:
                next_month = month_obj.replace(month=month_obj.month + 1)
            days_in_month = (next_month - month_obj).days
            avg_flights_per_day = (
                month_stat["flights_count"] / days_in_month if days_in_month > 0 else 0
            )

            monthly_data.append(
                {
                    "month": month_stat["month"].strftime("%Y-%m"),
                    "flights_count": month_stat["flights_count"],
                    "avg_flights_per_day": round(avg_flights_per_day),
                    "flight_density": round(month_density),
                    "total_duration_hours": round(month_total_hours),
                    "avg_duration_minutes": round(month_avg_minutes),
                    "median_duration_minutes": round(month_median_minutes),
                }
            )

        all_regions = list(
            RussianRegion.objects.values("id", "name", "code").order_by("name")
        )

        regions_with_activity_index = []
        current_year = date.today().year

        start_date = date(current_year, 1, 1)
        end_date = date(current_year, 12, 31)
        total_days_in_year = (end_date - start_date).days + 1

        for region in all_regions:
            region_id = region["id"]
            region_code = region["code"]

            region_flights = FlightPlan.objects.filter(
                departure_region__id=region_id, planned_date__year=current_year
            )

            flights_count = region_flights.count()
            total_duration = region_flights.aggregate(Sum("planned_duration"))[
                "planned_duration__sum"
            ]
            avg_duration = region_flights.aggregate(Avg("planned_duration"))[
                "planned_duration__avg"
            ]

            total_duration_hours = 0
            avg_duration_minutes = 0
            if total_duration:
                total_duration_hours = total_duration.total_seconds() / 3600
            if avg_duration:
                avg_duration_minutes = avg_duration.total_seconds() / 60

            region_area_km2 = region_areas.get(region_code, 1)
            flight_density = (
                (flights_count / region_area_km2) * 1000 if region_area_km2 > 0 else 0
            )

            all_flight_dates = set(
                region_flights.values_list("planned_date", flat=True)
            )
            zero_flight_days = total_days_in_year - len(all_flight_dates)

            durations = region_flights.exclude(
                planned_duration__isnull=True
            ).values_list("planned_duration", flat=True)
            duration_minutes = [d.total_seconds() / 60 for d in durations]
            median_duration = (
                statistics.median(duration_minutes) if duration_minutes else 0
            )

            FD = flight_density
            SPD = flights_count / total_days_in_year if total_days_in_year > 0 else 0
            GROW = 0.5
            CONT = (
                1 - (zero_flight_days / total_days_in_year)
                if total_days_in_year > 0
                else 0
            )
            DUR = avg_duration_minutes

            regions_with_activity_index.append(
                {
                    "region_id": region_id,
                    "region_name": region["name"],
                    "region_code": region_code,
                    "flights_count": flights_count,
                    "flight_density": round(flight_density),
                    "total_duration_hours": round(total_duration_hours),
                    "avg_duration_minutes": round(avg_duration_minutes),
                    "median_duration_minutes": round(median_duration),
                    "FD": FD,
                    "SPD": SPD,
                    "GROW": GROW,
                    "CONT": CONT,
                    "DUR": DUR,
                }
            )

        import numpy as np

        if regions_with_activity_index:

            fd_values = [r["FD"] for r in regions_with_activity_index]
            spd_values = [r["SPD"] for r in regions_with_activity_index]
            grow_values = [r["GROW"] for r in regions_with_activity_index]
            cont_values = [r["CONT"] for r in regions_with_activity_index]
            dur_values = [r["DUR"] for r in regions_with_activity_index]

            def normalize_metric(values):
                if not values or len(values) == 0:
                    return [0.5] * len(values)
                p10 = np.percentile(values, 10)
                p90 = np.percentile(values, 90)
                if p90 == p10:
                    return [0.5] * len(values)
                normalized = []
                for val in values:
                    norm_val = (val - p10) / (p90 - p10)
                    norm_val = max(0, min(1, norm_val))
                    normalized.append(norm_val)
                return normalized

            fd_normalized = normalize_metric(fd_values)
            spd_normalized = normalize_metric(spd_values)
            grow_normalized = normalize_metric(grow_values)
            cont_normalized = normalize_metric(cont_values)
            dur_normalized = normalize_metric(dur_values)

            all_activity_indexes = []
            for i, region_data in enumerate(regions_with_activity_index):
                activity_index = 100 * (
                        0.40 * fd_normalized[i]
                        + 0.22 * spd_normalized[i]
                        + 0.18 * grow_normalized[i]
                        + 0.10 * cont_normalized[i]
                        + 0.10 * dur_normalized[i]
                )
                region_data["activity_index"] = round(activity_index, 2)
                all_activity_indexes.append(activity_index)

            average_activity_index = (
                sum(all_activity_indexes) / len(all_activity_indexes)
                if all_activity_indexes
                else 0
            )

            top_regions_data = sorted(
                regions_with_activity_index,
                key=lambda x: x["activity_index"],
                reverse=True,
            )[:10]

            for region in top_regions_data:
                region.pop("FD", None)
                region.pop("SPD", None)
                region.pop("GROW", None)
                region.pop("CONT", None)
                region.pop("DUR", None)
        else:
            average_activity_index = 0
            top_regions_data = []

        individual_regions_data = []

        for region in all_regions:

            region_flights = FlightPlan.objects.filter(
                departure_region__id=region["id"]
            )

            flights_count = region_flights.count()
            total_duration = region_flights.aggregate(Sum("planned_duration"))[
                "planned_duration__sum"
            ]
            avg_duration = region_flights.aggregate(Avg("planned_duration"))[
                "planned_duration__avg"
            ]
            region_total_hours = 0
            region_avg_minutes = 0
            if total_duration:
                region_total_hours = total_duration.total_seconds() / 3600
            if avg_duration:
                region_avg_minutes = avg_duration.total_seconds() / 60

            region_code = region["code"]
            region_area_km2 = region_areas.get(region_code, 1)
            region_density = (
                (flights_count / region_area_km2) * 1000 if region_area_km2 > 0 else 0
            )

            region_median_minutes = 0
            if flights_count > 0:
                try:
                    with connection.cursor() as cursor:
                        cursor.execute(
                            """
                            SELECT EXTRACT(EPOCH FROM planned_duration) / 60 as duration_minutes
                            FROM flights_flightplan
                            WHERE planned_duration IS NOT NULL
                              AND departure_region_id = %s
                            ORDER BY planned_duration
                            LIMIT 1 OFFSET (SELECT COUNT(*) / 2
                                            FROM flights_flightplan
                                            WHERE planned_duration IS NOT NULL
                                              AND departure_region_id = %s)
                            """,
                            [region["id"], region["id"]],
                        )
                        result = cursor.fetchone()
                        if result:
                            region_median_minutes = result[0]
                except Exception:
                    pass

            individual_regions_data.append(
                {
                    "region_id": region["id"],
                    "region_name": region["name"],
                    "region_code": region_code,
                    "flights_count": flights_count,
                    "flight_density": round(region_density),
                    "total_duration_hours": round(region_total_hours),
                    "avg_duration_minutes": round(region_avg_minutes),
                    "median_duration_minutes": round(region_median_minutes),
                }
            )

        individual_regions_data = sorted(
            individual_regions_data, key=lambda x: x["region_name"]
        )

        regional_monthly_data = {}
        try:
            monthly_analysis_start = date.today().replace(day=1) - timedelta(days=365)
            monthly_analysis_end = date.today()

            all_months = []
            for month_entry in monthly_data:
                month_str = month_entry["month"]
                month_date = datetime.strptime(month_str, "%Y-%m").date().replace(day=1)
                all_months.append(month_date)

            all_regions_with_flights = (
                RussianRegion.objects.all()
                .values("id", "name", "code")
                .order_by("name")
            )

            for region_data in all_regions_with_flights:
                region_id = region_data["id"]
                region_code = region_data["code"]
                region_name = region_data["name"]

                monthly_region_stats = (
                    FlightPlan.objects.filter(
                        departure_region__code=region_code,
                        planned_date__gte=monthly_analysis_start,
                        planned_date__lte=monthly_analysis_end,
                    )
                    .annotate(month=TruncMonth("planned_date"))
                    .values("month")
                    .annotate(
                        flights_count=Count("id"),
                        total_duration=Sum("planned_duration"),
                        avg_duration=Avg("planned_duration"),
                    )
                    .order_by("month")
                )

                existing_data = {}
                for month_stat in monthly_region_stats:
                    existing_data[month_stat["month"]] = month_stat

                region_monthly_list = []
                region_area_km2 = region_areas.get(region_code, 1)

                for month in all_months:
                    if month in existing_data:
                        month_stat = existing_data[month]
                        month_total_hours = 0
                        month_avg_minutes = 0
                        if month_stat["total_duration"]:
                            month_total_hours = (
                                    month_stat["total_duration"].total_seconds() / 3600
                            )
                        if month_stat["avg_duration"]:
                            month_avg_minutes = (
                                    month_stat["avg_duration"].total_seconds() / 60
                            )

                        region_density = (
                            (month_stat["flights_count"] / region_area_km2) * 1000
                            if region_area_km2 > 0
                            else 0
                        )

                        month_median_minutes = 0
                        try:
                            with connection.cursor() as cursor:
                                cursor.execute(
                                    """
                                    SELECT EXTRACT(EPOCH FROM planned_duration) / 60 as duration_minutes
                                    FROM flights_flightplan
                                    WHERE planned_duration IS NOT NULL
                                      AND departure_region_id = (SELECT id
                                                                 FROM flights_russianregion
                                                                 WHERE code = %s)
                                      AND DATE_TRUNC('month', planned_date) = %s
                                    ORDER BY planned_duration
                                    LIMIT 1 OFFSET (SELECT COUNT(*) / 2
                                                    FROM flights_flightplan
                                                    WHERE planned_duration IS NOT NULL
                                                      AND
                                                        departure_region_id = (SELECT id
                                                                               FROM flights_russianregion
                                                                               WHERE code = %s)
                                                      AND DATE_TRUNC('month', planned_date) = %s)
                                    """,
                                    [
                                        region_code,
                                        month,
                                        region_code,
                                        month,
                                    ],
                                )
                                result = cursor.fetchone()
                                if result:
                                    month_median_minutes = result[0]
                        except Exception:
                            pass

                        if month.month == 12:
                            next_month = month.replace(year=month.year + 1, month=1)
                        else:
                            next_month = month.replace(month=month.month + 1)
                        days_in_month = (next_month - month).days
                        avg_flights_per_day = (
                            month_stat["flights_count"] / days_in_month
                            if days_in_month > 0
                            else 0
                        )

                        region_monthly_list.append(
                            {
                                "month": month.strftime("%Y-%m"),
                                "flights_count": month_stat["flights_count"],
                                "avg_flights_per_day": round(avg_flights_per_day),
                                "flight_density": round(region_density),
                                "total_duration_hours": round(month_total_hours),
                                "avg_duration_minutes": round(month_avg_minutes),
                                "median_duration_minutes": round(month_median_minutes),
                            }
                        )
                    else:
                        region_monthly_list.append(
                            {
                                "month": month.strftime("%Y-%m"),
                                "flights_count": 0,
                                "avg_flights_per_day": 0,
                                "flight_density": 0,
                                "total_duration_hours": 0,
                                "avg_duration_minutes": 0,
                                "median_duration_minutes": 0,
                            }
                        )

                total_flights_in_region = sum(
                    m["flights_count"] for m in region_monthly_list
                )
                avg_flights_per_month_region = (
                    total_flights_in_region / len(region_monthly_list)
                    if region_monthly_list
                    else 0
                )

                regional_monthly_data[str(region_id)] = {
                    "region_id": region_id,
                    "region_name": region_name,
                    "region_code": region_code,
                    "avg_flights_per_month": round(avg_flights_per_month_region),
                    "monthly_data": region_monthly_list,
                }
        except Exception:
            regional_monthly_data = {}

        quarterly_data = {"Q1": [], "Q2": [], "Q3": [], "Q4": []}
        try:
            current_year = date.today().year

            quarters = {
                "Q1": (date(current_year, 1, 1), date(current_year, 3, 31)),
                "Q2": (date(current_year, 4, 1), date(current_year, 6, 30)),
                "Q3": (date(current_year, 7, 1), date(current_year, 9, 30)),
                "Q4": (date(current_year, 10, 1), date(current_year, 12, 31)),
            }

            for quarter_name, (start_date, end_date) in quarters.items():
                quarter_list = []

                for region in all_regions:

                    region_flights = FlightPlan.objects.filter(
                        departure_region__id=region["id"],
                        planned_date__range=[start_date, end_date],
                    )

                    flights_count = region_flights.count()
                    total_duration = region_flights.aggregate(Sum("planned_duration"))[
                        "planned_duration__sum"
                    ]
                    avg_duration = region_flights.aggregate(Avg("planned_duration"))[
                        "planned_duration__avg"
                    ]
                    region_total_hours = 0
                    region_avg_minutes = 0
                    if total_duration:
                        region_total_hours = total_duration.total_seconds() / 3600
                    if avg_duration:
                        region_avg_minutes = avg_duration.total_seconds() / 60

                    region_code = region["code"]
                    region_area_km2 = region_areas.get(region_code, 1)
                    region_density = (
                        (flights_count / region_area_km2) * 1000
                        if region_area_km2 > 0
                        else 0
                    )

                    region_median_minutes = 0
                    if flights_count > 0:
                        try:
                            with connection.cursor() as cursor:
                                cursor.execute(
                                    """
                                    SELECT EXTRACT(EPOCH FROM planned_duration) / 60 as duration_minutes
                                    FROM flights_flightplan
                                    WHERE planned_duration IS NOT NULL
                                      AND departure_region_id = %s
                                      AND planned_date BETWEEN %s AND %s
                                    ORDER BY planned_duration
                                    LIMIT 1 OFFSET (SELECT COUNT(*) / 2
                                                    FROM flights_flightplan
                                                    WHERE planned_duration IS NOT NULL
                                                      AND departure_region_id = %s
                                                      AND planned_date BETWEEN %s AND %s)
                                    """,
                                    [
                                        region["id"],
                                        start_date,
                                        end_date,
                                        region["id"],
                                        start_date,
                                        end_date,
                                    ],
                                )
                                result = cursor.fetchone()
                                if result:
                                    region_median_minutes = result[0]
                        except Exception:
                            pass

                    flight_dates = set(
                        region_flights.values_list("planned_date", flat=True)
                    )

                    total_days_in_quarter = (end_date - start_date).days + 1

                    days_with_flights = len(flight_dates)

                    zero_flight_days = total_days_in_quarter - days_with_flights

                    avg_flights_per_day_quarter = (
                        flights_count / total_days_in_quarter
                        if total_days_in_quarter > 0
                        else 0
                    )

                    quarter_list.append(
                        {
                            "region_id": region["id"],
                            "region_name": region["name"],
                            "region_code": region_code,
                            "flights_count": flights_count,
                            "avg_flights_per_day": round(avg_flights_per_day_quarter),
                            "flight_density": round(region_density),
                            "total_duration_hours": round(region_total_hours),
                            "avg_duration_minutes": round(region_avg_minutes),
                            "median_duration_minutes": round(region_median_minutes),
                            "zero_flight_days": zero_flight_days,
                        }
                    )

                quarterly_data[quarter_name] = sorted(
                    quarter_list, key=lambda x: x["region_name"]
                )
        except Exception:
            quarterly_data = {"Q1": [], "Q2": [], "Q3": [], "Q4": []}

        avg_flights_per_month_overall = (
            sum(m["flights_count"] for m in monthly_data) / max(len(all_regions), 1)
            if monthly_data
            else 0
        )

        avg_flights_per_day_overall = (
            sum(m["avg_flights_per_day"] for m in monthly_data)
            / max(len(all_regions), 1)
            if monthly_data
            else 0
        )

        result = {
            "overall_statistics": {
                "total_flights_count": total_flights_count,
                "avg_flights_per_month": round(avg_flights_per_month_overall),
                "avg_flights_per_day": round(avg_flights_per_day_overall),
                "overall_flight_density": round(overall_flight_density),
                "total_duration_hours": round(total_duration_hours),
                "avg_duration_minutes": round(avg_duration_minutes),
                "median_duration_minutes": round(median_duration_minutes),
                "average_activity_index": round(average_activity_index, 2),
            },
            "monthly_statistics": monthly_data,
            "regional_monthly_statistics": regional_monthly_data,
            "top_10_regions_overall": top_regions_data,
            "individual_regions_statistics": individual_regions_data,
            "all_regions_quarterly": quarterly_data,
        }

        cache.set(cache_key, result, 3600)

        return Response(result)

    @extend_schema(
        operation_id="statistics_regional_annual",
        summary="Региональная годовая статистика полетов",
        description="Детальная статистика полетов БАС по каждому региону России за год",
        tags=["Регионы РФ"],
        parameters=[
            OpenApiParameter(
                name="year",
                type=OpenApiTypes.INT,
                location=OpenApiParameter.QUERY,
                description="Год для анализа (по умолчанию текущий год)"
            ),
        ]
    )
    @action(detail=False, methods=["get"])
    def regional_annual_statistics(self, request) -> Response:
        """
        Статистика по каждому региону за год с детализацией по времени суток.

        GET /api/statistics/regional_annual_statistics/
        """
        year = request.query_params.get("year")
        if not year:
            year = date.today().year
        else:
            try:
                year = int(year)
            except ValueError:
                return Response(
                    {"error": "Неверный формат года"},
                    status=status.HTTP_400_BAD_REQUEST,
                )

        year_flights = FlightPlan.objects.filter(planned_date__year=year)

        all_regions = list(
            RussianRegion.objects.values("id", "name", "code").order_by("name")
        )

        regional_metrics = []
        regional_data = []

        start_date = date(year, 1, 1)
        end_date = date(year, 12, 31)
        total_days_in_year = (end_date - start_date).days + 1

        for region in all_regions:
            region_id = region["id"]
            region_code = region["code"]
            region_flights = year_flights.filter(departure_region__id=region_id)

            flights_count = region_flights.count()
            total_duration = region_flights.aggregate(Sum("planned_duration"))[
                "planned_duration__sum"
            ]
            avg_duration = region_flights.aggregate(Avg("planned_duration"))[
                "planned_duration__avg"
            ]

            total_duration_hours = 0
            avg_duration_minutes = 0

            if total_duration:
                total_duration_hours = total_duration.total_seconds() / 3600
            if avg_duration:
                avg_duration_minutes = avg_duration.total_seconds() / 60

            try:
                region_obj = RussianRegion.objects.filter(code=region_code).first()
                if region_obj and region_obj.area and region_obj.area.strip():

                    region_area_km2 = float(region_obj.area.replace(",", "."))
                else:
                    region_area_km2 = 1
            except (ValueError, AttributeError):
                region_area_km2 = 1

            try:
                flight_density = (
                    (flights_count / region_area_km2) * 1000
                    if region_area_km2 and region_area_km2 > 0
                    else 0
                )
            except (TypeError, ZeroDivisionError):
                flight_density = 0

            durations = region_flights.exclude(
                planned_duration__isnull=True
            ).values_list("planned_duration", flat=True)
            duration_minutes = [d.total_seconds() / 60 for d in durations]
            median_duration = (
                statistics.median(duration_minutes) if duration_minutes else 0
            )

            all_flight_dates = set(
                region_flights.values_list("planned_date", flat=True)
            )
            start_date = date(year, 1, 1)
            end_date = date(year, 12, 31)
            total_days_in_year = (end_date - start_date).days + 1

            days_with_flights = len(all_flight_dates)
            zero_flight_days = total_days_in_year - days_with_flights

            morning_flights = region_flights.filter(
                planned_departure_time__hour__gte=6, planned_departure_time__hour__lt=12
            ).count()

            day_flights = region_flights.filter(
                planned_departure_time__hour__gte=12,
                planned_departure_time__hour__lt=18,
            ).count()

            evening_flights = (
                    region_flights.filter(
                        planned_departure_time__hour__gte=18,
                        planned_departure_time__hour__lt=24,
                    ).count()
                    + region_flights.filter(
                planned_departure_time__hour__gte=0,
                planned_departure_time__hour__lt=6,
            ).count()
            )

            FD = flight_density

            FpD = flights_count / total_days_in_year if total_days_in_year > 0 else 0

            GROW = 0.5

            days_with_flights = len(all_flight_dates)
            CONT = (
                1 - (zero_flight_days / total_days_in_year)
                if total_days_in_year > 0
                else 0
            )

            DUR = avg_duration_minutes

            metrics = {
                "region_code": region_code,
                "FD": FD,
                "FpD": FpD,
                "GROW": GROW,
                "CONT": CONT,
                "DUR": DUR,
            }
            regional_metrics.append(metrics)

            avg_flights_per_year = flights_count

            avg_flights_per_month = flights_count / 12

            avg_flights_per_day = flights_count / total_days_in_year

            regional_data.append(
                {
                    "region_id": region_id,
                    "region_name": region["name"],
                    "region_code": region_code,
                    "year": year,
                    "flights_count": flights_count,
                    "avg_flights_per_year": round(avg_flights_per_year),
                    "avg_flights_per_month": round(avg_flights_per_month),
                    "avg_flights_per_day": round(avg_flights_per_day),
                    "flight_density": round(flight_density),
                    "total_duration_hours": round(total_duration_hours),
                    "avg_duration_minutes": round(avg_duration_minutes),
                    "median_duration_minutes": round(median_duration),
                    "zero_flight_days": zero_flight_days,
                    "time_distribution": {
                        "morning_flights": morning_flights,  # 6:00-12:00
                        "day_flights": day_flights,  # 12:00-18:00
                        "evening_flights": evening_flights,  # 18:00-6:00
                    },
                }
            )

        import numpy as np

        if regional_metrics:

            fd_values = [m["FD"] for m in regional_metrics]
            fpd_values = [m["FpD"] for m in regional_metrics]
            grow_values = [m["GROW"] for m in regional_metrics]
            cont_values = [m["CONT"] for m in regional_metrics]
            dur_values = [m["DUR"] for m in regional_metrics]

            def normalize_metric(values):
                if not values or len(values) == 0:
                    return [0.5] * len(values)

                p10 = np.percentile(values, 10)
                p90 = np.percentile(values, 90)

                if p90 == p10:
                    return [0.5] * len(values)

                normalized = []
                for val in values:
                    norm_val = (val - p10) / (p90 - p10)
                    norm_val = max(0, min(1, norm_val))
                    normalized.append(norm_val)

                return normalized

            fd_normalized = normalize_metric(fd_values)
            fpd_normalized = normalize_metric(fpd_values)
            grow_normalized = normalize_metric(grow_values)
            cont_normalized = normalize_metric(cont_values)
            dur_normalized = normalize_metric(dur_values)

            for i, region_data in enumerate(regional_data):

                if region_data["flights_count"] == 0:
                    region_data["activity_index"] = 0
                else:

                    # Весовые коэффициенты согласно спецификации
                    w_fd = 0.40  # FD имеет наибольший вес (40%)
                    w_fpd = 0.22  # FpD - среднесуточный темп (22%)
                    w_grow = 0.18  # GROW - рост активности (18%)
                    w_cont = 0.10  # CONT - непрерывность (10%)
                    w_dur = 0.10  # DUR - средняя длительность (10%)

                    activity_index = 100 * (
                            w_fd * fd_normalized[i]
                            + w_fpd * fpd_normalized[i]
                            + w_grow * grow_normalized[i]
                            + w_cont * cont_normalized[i]
                            + w_dur * dur_normalized[i]
                    )

                    region_data["activity_index"] = round(activity_index, 2)

        regional_data_sorted = sorted(
            regional_data, key=lambda x: x.get("activity_index", 0), reverse=True
        )

        for i, region_data in enumerate(regional_data_sorted):
            region_data["rating"] = i + 1

        regional_data = sorted(regional_data_sorted, key=lambda x: x["region_name"])

        summary_stats = {
            "total_flights_all_regions": sum(
                r["flights_count"] for r in regional_data
            ),
            "avg_flights_per_region_per_year": round(
                sum(r["flights_count"] for r in regional_data)
                / max(len(regional_data), 1)
            ),
            "avg_flights_per_region_per_month": round(
                sum(r["avg_flights_per_month"] for r in regional_data)
                / max(len(regional_data), 1)
            ),
            "avg_flights_per_region_per_day": round(
                sum(r["avg_flights_per_day"] for r in regional_data)
                / max(len(regional_data), 1)
            ),
        }

        return Response(
            {
                "year": year,
                "total_regions": len(regional_data),
                "summary": summary_stats,
                "regional_statistics": regional_data,
            }
        )

    @extend_schema(exclude=True)
    @action(detail=False, methods=["get"])
    def export_data(self, request) -> Response:
        """
        Экспорт статистических данных.

        GET /api/statistics/export_data/?format=json|csv
        """
        export_format = request.query_params.get("format", "json")
        date_from = request.query_params.get("date_from")
        date_to = request.query_params.get("date_to")

        queryset = FlightPlan.objects.select_related(
            "operator", "drone_type", "departure_region", "destination_region"
        )

        if date_from:
            try:
                date_from = datetime.strptime(date_from, "%Y-%m-%d").date()
                queryset = queryset.filter(planned_date__gte=date_from)
            except ValueError:
                pass

        if date_to:
            try:
                date_to = datetime.strptime(date_to, "%Y-%m-%d").date()
                queryset = queryset.filter(planned_date__lte=date_to)
            except ValueError:
                pass

        if export_format == "csv":
            import csv
            from io import StringIO

            output = StringIO()
            writer = csv.writer(output)

            writer.writerow(
                [
                    "ID полета",
                    "Дата",
                    "Время вылета",
                    "Оператор",
                    "Тип БАС",
                    "Регион вылета",
                    "Регион назначения",
                    "Продолжительность (мин)",
                    "Статус",
                ]
            )

            for flight in queryset[:1000]:
                try:
                    status = flight.actualflight.flight_status
                except:
                    status = "planned"

                writer.writerow(
                    [
                        flight.flight_id,
                        flight.planned_date,
                        flight.planned_departure_time,
                        flight.operator.name,
                        flight.drone_type.code,
                        flight.departure_region.name if flight.departure_region else "",
                        (
                            flight.destination_region.name
                            if flight.destination_region
                            else ""
                        ),
                        (
                            int(flight.planned_duration.total_seconds() / 60)
                            if flight.planned_duration
                            else 0
                        ),
                        status,
                    ]
                )

            response = HttpResponse(output.getvalue(), content_type="text/csv")
            response["Content-Disposition"] = (
                f'attachment; filename="flights_export_{date.today()}.csv"'
            )
            return response

        else:
            serializer = FlightPlanSerializer(queryset[:1000], many=True)
            return Response(
                {
                    "flights": serializer.data,
                    "exported_at": timezone.now().isoformat(),
                    "total_count": len(serializer.data),
                }
            )

    @extend_schema(
        summary="Анализ роста/падения полетов по месяцам")
    @action(detail=False, methods=["get"])
    def growth_trends(self, request) -> Response:
        """
        Анализ роста/падения полетов по месяцам.

        GET /api/statistics/growth_trends/
        """
        current_month = request.query_params.get("month")

        try:
            if current_month:
                current_month = (
                    datetime.strptime(current_month, "%Y-%m-%d").date().replace(day=1)
                )
            else:
                current_month = date.today().replace(day=1)

            result = AdvancedAnalyticsService.get_growth_decline_statistics(
                current_month
            )
            return Response(result)

        except ValueError:
            return Response(
                {"error": "Неверный формат месяца. Используйте YYYY-MM-DD"},
                status=status.HTTP_400_BAD_REQUEST,
            )

    @extend_schema(tags=["Дашборд и метрики"], summary="Анализ дней без полетов по регионам")
    @action(detail=False, methods=["get"])
    def zero_flight_days_analysis(self, request) -> Response:
        """
        Анализ дней без полетов по регионам.
        Анализируются только регионы из планов полетов.

        GET /api/statistics/zero_flight_days_analysis/

        Query параметры:
        - date_from: дата начала анализа (YYYY-MM-DD)
        - date_to: дата окончания анализа (YYYY-MM-DD)
        - top: количество топ регионов для отображения (по умолчанию 20)
        """
        date_from = request.query_params.get("date_from")
        date_to = request.query_params.get("date_to")
        top = int(request.query_params.get("top", 20))

        try:
            if date_from:
                date_from = datetime.strptime(date_from, "%Y-%m-%d").date()
            if date_to:
                date_to = datetime.strptime(date_to, "%Y-%m-%d").date()

            result = AdvancedAnalyticsService.get_zero_flight_days_by_regions(
                date_from, date_to
            )

            total_regions = len(result)
            regions_with_flights_in_period = len(
                [r for r in result if r["total_flights"] > 0]
            )
            regions_without_flights_in_period = len(
                [r for r in result if r["total_flights"] == 0]
            )
            regions_with_zero_days = len(
                [r for r in result if r["zero_flight_days"] > 0]
            )
            regions_with_full_activity = len(
                [r for r in result if r["zero_flight_days"] == 0]
            )

            top_zero_days = result[:top]

            most_active_regions = sorted(result, key=lambda x: x["zero_flight_days"])[
                :top
            ]

            return Response(
                {
                    "analysis_period": {
                        "date_from": date_from.isoformat() if date_from else None,
                        "date_to": date_to.isoformat() if date_to else None,
                        "total_days": result[0]["total_days_analyzed"] if result else 0,
                    },
                    "summary": {
                        "total_regions_analyzed": total_regions,
                        "regions_with_flights_in_period": regions_with_flights_in_period,
                        "regions_without_flights_in_period": regions_without_flights_in_period,
                        "regions_with_zero_days": regions_with_zero_days,
                        "regions_with_full_activity": regions_with_full_activity,
                        "note": "Анализируются только регионы из планов полетов, регионы без полетов не включены",
                    },
                    "top_regions_with_zero_days": top_zero_days,
                    "most_active_regions": most_active_regions,
                    "statistics": {
                        "avg_zero_days": round(
                            sum(r["zero_flight_days"] for r in result)
                            / max(len(result), 1),
                            2,
                        ),
                        "median_zero_days": (
                            sorted([r["zero_flight_days"] for r in result])[
                                len(result) // 2
                                ]
                            if result
                            else 0
                        ),
                        "max_zero_days": max(
                            (r["zero_flight_days"] for r in result), default=0
                        ),
                        "min_zero_days": min(
                            (r["zero_flight_days"] for r in result), default=0
                        ),
                        "total_flights_analyzed": sum(
                            r["total_flights"] for r in result
                        ),
                        "avg_flights_per_region": round(
                            sum(r["total_flights"] for r in result)
                            / max(len(result), 1),
                            2,
                        ),
                    },
                }
            )

        except ValueError:
            return Response(
                {"error": "Неверный формат даты. Используйте YYYY-MM-DD"},
                status=status.HTTP_400_BAD_REQUEST,
            )
        except Exception as e:
            logger.error(f"Ошибка анализа дней без полетов: {e}")
            return Response(
                {"error": f"Ошибка анализа: {str(e)}"},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR,
            )

    @extend_schema(
        summary="Все расширенные метрики в одном ответе",
    )
    @action(detail=False, methods=["get"])
    def comprehensive_metrics(self, request) -> Response:
        """
        Все расширенные метрики в одном ответе.

        GET /api/statistics/comprehensive_metrics/
        """
        date_from = request.query_params.get("date_from")
        date_to = request.query_params.get("date_to")

        try:
            if date_from:
                date_from = datetime.strptime(date_from, "%Y-%m-%d").date()
            if date_to:
                date_to = datetime.strptime(date_to, "%Y-%m-%d").date()

            result = AdvancedAnalyticsService.get_comprehensive_analytics(
                date_from, date_to
            )
            return Response(result)

        except ValueError:
            return Response(
                {"error": "Неверный формат даты"}, status=status.HTTP_400_BAD_REQUEST
            )
        except Exception as e:
            return Response(
                {"error": str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )

    @extend_schema(tags=["Регионы РФ"],
                   summary="Анализ роста/падения полетов по регионам за месяц", )
    @action(detail=False, methods=["get"])
    def regional_growth_trends(self, request) -> Response:
        """
        Анализ роста/падения полетов по регионам за месяц.
        Для каждого региона отдельно рассчитывается процент изменения.

        GET /api/statistics/regional_growth_trends/

        Query параметры:
        - month: месяц для анализа (YYYY-MM-DD, по умолчанию текущий месяц)
        """
        current_month = request.query_params.get("month")

        try:
            if current_month:
                current_month = (
                    datetime.strptime(current_month, "%Y-%m-%d").date().replace(day=1)
                )
            else:
                current_month = date.today().replace(day=1)

            result = AdvancedAnalyticsService.get_regional_growth_trends(current_month)
            return Response(result)

        except ValueError:
            return Response(
                {"error": "Неверный формат месяца. Используйте YYYY-MM-DD"},
                status=status.HTTP_400_BAD_REQUEST,
            )
        except Exception as e:
            logger.error(f"Ошибка анализа региональных трендов роста: {e}")
            return Response(
                {"error": f"Ошибка анализа: {str(e)}"},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR,
            )

    @extend_schema(tags=["Дашборд и метрики"],
                   summary="Экспорт региональной годовой статистики в Excel файл")
    @action(detail=False, methods=["get"])
    def export_regional_annual_excel(self, request) -> Response:
        """
        Экспорт региональной годовой статистики в Excel файл.

        GET /api/statistics/export_regional_annual_excel/?year=2024

        Query параметры:
        - year: год для экспорта (по умолчанию текущий год)
        """
        import io

        import pandas as pd
        from django.http import HttpResponse

        year = request.query_params.get("year")
        if not year:
            year = date.today().year
        else:
            try:
                year = int(year)
            except ValueError:
                return Response(
                    {"error": "Неверный формат года"},
                    status=status.HTTP_400_BAD_REQUEST,
                )

        try:

            year_flights = FlightPlan.objects.filter(planned_date__year=year)

            all_regions = list(
                RussianRegion.objects.values("id", "name", "code").order_by("name")
            )

            regional_metrics = []
            regional_data = []

            start_date = date(year, 1, 1)
            end_date = date(year, 12, 31)
            total_days_in_year = (end_date - start_date).days + 1

            excel_data = []
            row_number = 1

            for region in all_regions:
                region_id = region["id"]
                region_code = region["code"]
                region_flights = year_flights.filter(departure_region__id=region_id)

                flights_count = region_flights.count()
                total_duration = region_flights.aggregate(Sum("planned_duration"))[
                    "planned_duration__sum"
                ]
                avg_duration = region_flights.aggregate(Avg("planned_duration"))[
                    "planned_duration__avg"
                ]

                total_duration_hours = 0
                avg_duration_minutes = 0

                if total_duration:
                    total_duration_hours = total_duration.total_seconds() / 3600
                if avg_duration:
                    avg_duration_minutes = avg_duration.total_seconds() / 60

                try:
                    region_obj = RussianRegion.objects.filter(code=region_code).first()
                    if region_obj and region_obj.area and region_obj.area.strip():
                        region_area_km2 = float(region_obj.area.replace(",", "."))
                    else:
                        region_area_km2 = 1
                except (ValueError, AttributeError):
                    region_area_km2 = 1

                try:
                    flight_density = (
                        (flights_count / region_area_km2) * 1000
                        if region_area_km2 and region_area_km2 > 0
                        else 0
                    )
                except (TypeError, ZeroDivisionError):
                    flight_density = 0

                durations = region_flights.exclude(
                    planned_duration__isnull=True
                ).values_list("planned_duration", flat=True)
                duration_minutes = [d.total_seconds() / 60 for d in durations]
                median_duration = (
                    statistics.median(duration_minutes) if duration_minutes else 0
                )

                all_flight_dates = set(
                    region_flights.values_list("planned_date", flat=True)
                )
                start_date = date(year, 1, 1)
                end_date = date(year, 12, 31)
                total_days_in_year = (end_date - start_date).days + 1

                days_with_flights = len(all_flight_dates)
                zero_flight_days = total_days_in_year - days_with_flights

                morning_flights = region_flights.filter(
                    planned_departure_time__hour__gte=6,
                    planned_departure_time__hour__lt=12,
                ).count()

                day_flights = region_flights.filter(
                    planned_departure_time__hour__gte=12,
                    planned_departure_time__hour__lt=18,
                ).count()

                evening_flights = (
                        region_flights.filter(
                            planned_departure_time__hour__gte=18,
                            planned_departure_time__hour__lt=24,
                        ).count()
                        + region_flights.filter(
                    planned_departure_time__hour__gte=0,
                    planned_departure_time__hour__lt=6,
                ).count()
                )

                time_distribution = f"{morning_flights}/{day_flights}/{evening_flights}"

                FD = flight_density

                SPD = (
                    flights_count / total_days_in_year if total_days_in_year > 0 else 0
                )

                GROW = 0.5

                days_with_flights = len(all_flight_dates)
                CONT = (
                    1 - (zero_flight_days / total_days_in_year)
                    if total_days_in_year > 0
                    else 0
                )

                DUR = avg_duration_minutes

                metrics = {
                    "region_code": region_code,
                    "FD": FD,
                    "SPD": SPD,
                    "GROW": GROW,
                    "CONT": CONT,
                    "DUR": DUR,
                }
                regional_metrics.append(metrics)

                excel_data.append(
                    {
                        "№": row_number,
                        "Наименование региона": region["name"],
                        "Количество полетов": flights_count,
                        "Плотность полетов": round(flight_density),
                        "Длительность полетов": round(total_duration_hours),
                        "Средняя длительности полетов": round(avg_duration_minutes),
                        "Медиана длительности полетов": round(median_duration),
                        "Нулевые дни": zero_flight_days,
                        "Количество полетов утро/день/вечер": time_distribution,
                    }
                )
                row_number += 1

            import numpy as np

            if regional_metrics:

                fd_values = [m["FD"] for m in regional_metrics]
                spd_values = [m["SPD"] for m in regional_metrics]
                grow_values = [m["GROW"] for m in regional_metrics]
                cont_values = [m["CONT"] for m in regional_metrics]
                dur_values = [m["DUR"] for m in regional_metrics]

                def normalize_metric(values):
                    if not values or len(values) == 0:
                        return [0.5] * len(values)

                    p10 = np.percentile(values, 10)
                    p90 = np.percentile(values, 90)

                    if p90 == p10:
                        return [0.5] * len(values)

                    normalized = []
                    for value in values:
                        norm_value = (value - p10) / (p90 - p10)
                        norm_value = max(0, min(1, norm_value))
                        normalized.append(norm_value)

                    return normalized

                fd_normalized = normalize_metric(fd_values)
                spd_normalized = normalize_metric(spd_values)
                grow_normalized = normalize_metric(grow_values)
                cont_normalized = normalize_metric(cont_values)
                dur_normalized = normalize_metric(dur_values)

                for i, metrics in enumerate(regional_metrics):

                    if excel_data[i]["Количество полетов"] == 0:
                        excel_data[i]["Индекс активности"] = 0
                    else:
                        activity_index = (
                                0.40 * fd_normalized[i]
                                + 0.22 * spd_normalized[i]
                                + 0.18 * grow_normalized[i]
                                + 0.10 * cont_normalized[i]
                                + 0.10 * dur_normalized[i]
                        )

                        excel_data[i]["Индекс активности"] = round(
                            activity_index * 100, 2
                        )
            else:

                for data in excel_data:
                    data["activity_index"] = 0

            df = pd.DataFrame(excel_data)

            output = io.BytesIO()
            with pd.ExcelWriter(output, engine="openpyxl") as writer:
                df.to_excel(
                    writer,
                    sheet_name=f"Статистика_{year}",
                    index=False,
                    columns=[
                        "№",
                        "Наименование региона",
                        "Индекс активности",
                        "Количество полетов",
                        "Плотность полетов",
                        "Длительность полетов",
                        "Средняя длительности полетов",
                        "Медиана длительности полетов",
                        "Нулевые дни",
                        "Количество полетов утро/день/вечер",
                    ],
                )

                worksheet = writer.sheets[f"Статистика_{year}"]
                worksheet.column_dimensions["A"].width = 8
                worksheet.column_dimensions["B"].width = 25
                worksheet.column_dimensions["C"].width = 15
                worksheet.column_dimensions["D"].width = 15
                worksheet.column_dimensions["E"].width = 18
                worksheet.column_dimensions["F"].width = 18
                worksheet.column_dimensions["G"].width = 20
                worksheet.column_dimensions["H"].width = 15
                worksheet.column_dimensions["I"].width = 20
                worksheet.column_dimensions["J"].width = 15

            output.seek(0)

            response = HttpResponse(
                output.getvalue(),
                content_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
            )
            response["Content-Disposition"] = (
                f'attachment; filename="regional_annual_statistics_{year}.xlsx"'
            )

            return response

        except Exception as e:
            logger.error(f"Ошибка экспорта Excel: {e}")
            return Response(
                {"error": f"Ошибка создания Excel файла: {str(e)}"},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR,
            )

@extend_schema(tags=["Операторы БАС"])
class DroneOperatorViewSet(viewsets.ReadOnlyModelViewSet):
    """ViewSet для операторов БАС."""

    queryset = DroneOperator.objects.annotate(flights_count=Count("flightplan"))
    serializer_class = DroneOperatorSerializer
    permission_classes = [permissions.IsAuthenticatedOrReadOnly]

    filter_backends = [filters.SearchFilter, filters.OrderingFilter]
    search_fields = ["name", "organization_type"]
    ordering = ["name"]


@extend_schema(tags=["Типы БАС"])
class DroneTypeViewSet(viewsets.ReadOnlyModelViewSet):
    """ViewSet для типов БАС."""

    queryset = DroneType.objects.annotate(flights_count=Count("flightplan"))
    serializer_class = DroneTypeSerializer
    permission_classes = [permissions.IsAuthenticatedOrReadOnly]

    ordering = ["code"]


@extend_schema(tags=["Регионы РФ"])
class RussianRegionViewSet(viewsets.ReadOnlyModelViewSet):
    """ViewSet для регионов РФ."""

    queryset = RussianRegion.objects.all()
    serializer_class = RussianRegionSerializer
    permission_classes = [permissions.IsAuthenticatedOrReadOnly]
    lookup_field = "code"
    pagination_class = None

    filter_backends = [filters.SearchFilter]
    search_fields = ["name", "code"]
    ordering = ["name"]
