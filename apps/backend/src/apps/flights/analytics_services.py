"""
Сервисы для расчета расширенных аналитических метрик.
"""

import logging
from calendar import monthrange
from datetime import date, timedelta
from statistics import median

from django.db.models import Avg, Count

from .models import FlightPlan, RussianRegion

logger = logging.getLogger(__name__)


class AdvancedAnalyticsService:
    """Сервис для расчета расширенных метрик полетов."""

    @classmethod
    def get_peak_load_statistics(
        cls, date_from: date = None, date_to: date = None
    ) -> dict:
        """
        Пиковая нагрузка: максимальное число полетов за час.

        Returns:
            Dict с информацией о пиковых нагрузках
        """
        queryset = FlightPlan.objects.all()
        if date_from and date_to:
            queryset = queryset.filter(planned_date__range=[date_from, date_to])
        elif date_from:
            queryset = queryset.filter(planned_date__gte=date_from)
        elif date_to:
            queryset = queryset.filter(planned_date__lte=date_to)

        hourly_stats = (
            queryset.extra(
                select={
                    "date_hour": "DATE_TRUNC('hour', planned_date::timestamp + planned_departure_time::interval)"
                }
            )
            .values("date_hour")
            .annotate(flights_count=Count("id"))
            .order_by("-flights_count")
        )

        if not hourly_stats:
            return {
                "peak_hour": None,
                "max_flights_per_hour": 0,
                "average_flights_per_hour": 0,
                "total_hours_analyzed": 0,
            }

        peak_stat = hourly_stats.first()
        total_flights = sum(stat["flights_count"] for stat in hourly_stats)
        total_hours = len(hourly_stats)

        return {
            "peak_hour": peak_stat["date_hour"],
            "max_flights_per_hour": peak_stat["flights_count"],
            "average_flights_per_hour": round(total_flights / max(total_hours, 1), 2),
            "total_hours_analyzed": total_hours,
            "peak_statistics": list(hourly_stats[:10]),
        }

    @classmethod
    def get_daily_dynamics(cls, date_from: date = None, date_to: date = None) -> dict:
        """
        Среднесуточная динамика: среднее и медианное число полетов в сутки.
        """
        queryset = FlightPlan.objects.all()
        if date_from and date_to:
            queryset = queryset.filter(planned_date__range=[date_from, date_to])
        elif date_from:
            queryset = queryset.filter(planned_date__gte=date_from)
        elif date_to:
            queryset = queryset.filter(planned_date__lte=date_to)

        daily_stats = (
            queryset.values("planned_date")
            .annotate(flights_count=Count("id"))
            .order_by("planned_date")
        )

        if not daily_stats:
            return {
                "average_flights_per_day": 0,
                "median_flights_per_day": 0,
                "min_flights_per_day": 0,
                "max_flights_per_day": 0,
                "zero_flight_days": 0,
                "total_days_analyzed": 0,
            }

        flights_per_day = [stat["flights_count"] for stat in daily_stats]

        if date_from and date_to:
            total_days = (date_to - date_from).days + 1
        else:
            first_flight = FlightPlan.objects.order_by("planned_date").first()
            last_flight = FlightPlan.objects.order_by("-planned_date").first()
            if first_flight and last_flight:
                total_days = (
                    last_flight.planned_date - first_flight.planned_date
                ).days + 1
            else:
                total_days = 1

        days_with_flights = len(daily_stats)
        zero_flight_days = total_days - days_with_flights

        return {
            "average_flights_per_day": round(
                sum(flights_per_day) / len(flights_per_day), 2
            ),
            "median_flights_per_day": median(flights_per_day),
            "min_flights_per_day": min(flights_per_day),
            "max_flights_per_day": max(flights_per_day),
            "zero_flight_days": zero_flight_days,
            "total_days_analyzed": total_days,
            "daily_breakdown": list(daily_stats),
        }

    @classmethod
    def get_growth_decline_statistics(cls, current_month: date = None) -> dict:
        """
        Рост/падение: процентное изменение числа полетов за месяц.
        """
        if not current_month:
            current_month = date.today().replace(day=1)

        if current_month.month == 1:
            previous_month = current_month.replace(
                year=current_month.year - 1, month=12
            )
        else:
            previous_month = current_month.replace(month=current_month.month - 1)

        current_month_end = current_month.replace(
            day=monthrange(current_month.year, current_month.month)[1]
        )
        previous_month_end = previous_month.replace(
            day=monthrange(previous_month.year, previous_month.month)[1]
        )

        current_flights = FlightPlan.objects.filter(
            planned_date__range=[current_month, current_month_end]
        ).count()

        previous_flights = FlightPlan.objects.filter(
            planned_date__range=[previous_month, previous_month_end]
        ).count()

        if previous_flights == 0:
            growth_rate = 100.0 if current_flights > 0 else 0.0
        else:
            growth_rate = (
                (current_flights - previous_flights) / previous_flights
            ) * 100

        return {
            "current_month": {"date": current_month, "flights_count": current_flights},
            "previous_month": {
                "date": previous_month,
                "flights_count": previous_flights,
            },
            "growth_rate_percent": round(growth_rate, 2),
            "absolute_change": current_flights - previous_flights,
            "trend": (
                "рост"
                if growth_rate > 0
                else "падение" if growth_rate < 0 else "стабильно"
            ),
        }

    @classmethod
    def get_flight_density_by_regions(
        cls, date_from: date = None, date_to: date = None
    ) -> list[dict]:
        """
        FlightDensity: число полетов на 1000км² территории региона.
        """
        queryset = FlightPlan.objects.filter(departure_region__isnull=False)
        if date_from and date_to:
            queryset = queryset.filter(planned_date__range=[date_from, date_to])
        elif date_from:
            queryset = queryset.filter(planned_date__gte=date_from)
        elif date_to:
            queryset = queryset.filter(planned_date__lte=date_to)

        regional_stats = queryset.values(
            "departure_region__id",
            "departure_region__code",
            "departure_region__name",
            "departure_region__area",
        ).annotate(flights_count=Count("id"))

        density_stats = []
        for stat in regional_stats:
            region_code = stat["departure_region__code"]
            region_area_raw = stat.get("departure_region__area")

            if region_area_raw and region_area_raw.strip():
                try:
                    region_area = float(region_area_raw.replace(",", "."))
                except (ValueError, AttributeError):
                    region_area = 1
            else:
                region_area = 1

            if region_area and region_area > 0:
                density = (stat["flights_count"] / region_area) * 1000  # на 1000 км²
                density_stats.append(
                    {
                        "region_id": stat["departure_region__id"],
                        "region_code": region_code,
                        "region_name": stat["departure_region__name"],
                        "flights_count": stat["flights_count"],
                        "area_km2": region_area,
                        "density_per_1000km2": round(density),
                    }
                )

        density_stats.sort(key=lambda x: x["density_per_1000km2"], reverse=True)

        return density_stats

    @classmethod
    def get_daily_activity_distribution(
        cls, date_from: date = None, date_to: date = None
    ) -> dict:
        """
        Дневная активность: распределение полетов по часам (утро/день/вечер).
        """
        queryset = FlightPlan.objects.all()
        if date_from and date_to:
            queryset = queryset.filter(planned_date__range=[date_from, date_to])
        elif date_from:
            queryset = queryset.filter(planned_date__gte=date_from)
        elif date_to:
            queryset = queryset.filter(planned_date__lte=date_to)

        hourly_stats = (
            queryset.extra(select={"hour": "EXTRACT(hour FROM planned_departure_time)"})
            .values("hour")
            .annotate(flights_count=Count("id"))
            .order_by("hour")
        )

        hours_data = dict.fromkeys(range(24), 0)
        for stat in hourly_stats:
            if stat["hour"] is not None:
                hours_data[int(stat["hour"])] = stat["flights_count"]

        # Группировка по периодам дня
        morning_flights = sum(hours_data[h] for h in range(6, 12))  # 6:00-11:59
        afternoon_flights = sum(hours_data[h] for h in range(12, 18))  # 12:00-17:59
        evening_flights = sum(hours_data[h] for h in range(18, 23))  # 18:00-22:59
        night_flights = sum(hours_data[h] for h in [23, 0, 1, 2, 3, 4, 5])  # 23:00-5:59

        total_flights = sum(hours_data.values())

        return {
            "hourly_distribution": [
                {"hour": hour, "flights_count": count}
                for hour, count in hours_data.items()
            ],
            "period_distribution": {
                "morning": {
                    "period": "Утро (6:00-11:59)",
                    "flights_count": morning_flights,
                    "percentage": round(
                        (morning_flights / max(total_flights, 1)) * 100, 2
                    ),
                },
                "afternoon": {
                    "period": "День (12:00-17:59)",
                    "flights_count": afternoon_flights,
                    "percentage": round(
                        (afternoon_flights / max(total_flights, 1)) * 100, 2
                    ),
                },
                "evening": {
                    "period": "Вечер (18:00-22:59)",
                    "flights_count": evening_flights,
                    "percentage": round(
                        (evening_flights / max(total_flights, 1)) * 100, 2
                    ),
                },
                "night": {
                    "period": "Ночь (23:00-5:59)",
                    "flights_count": night_flights,
                    "percentage": round(
                        (night_flights / max(total_flights, 1)) * 100, 2
                    ),
                },
            },
            "peak_hour": (
                max(hours_data.items(), key=lambda x: x[1])[0]
                if total_flights > 0
                else None
            ),
            "total_flights": total_flights,
        }

    @classmethod
    def get_zero_flight_days_by_regions(
        cls, date_from: date = None, date_to: date = None
    ) -> list[dict]:
        """
        Нулевые дни: количество дней без полетов по субъекту.
        Анализируются только регионы, которые имеют хотя бы один план полета.
        """
        if date_from and date_to:
            total_days = (date_to - date_from).days + 1
        else:
            first_flight = FlightPlan.objects.order_by("planned_date").first()
            last_flight = FlightPlan.objects.order_by("-planned_date").first()
            if first_flight and last_flight:
                total_days = (
                    last_flight.planned_date - first_flight.planned_date
                ).days + 1
                if not date_from:
                    date_from = first_flight.planned_date
                if not date_to:
                    date_to = last_flight.planned_date
            else:
                total_days = 1

        all_regions_with_flights = (
            FlightPlan.objects.filter(departure_region__isnull=False)
            .values(
                "departure_region__id",
                "departure_region__code",
                "departure_region__name",
            )
            .distinct("departure_region__code")
            .order_by("departure_region__code")
        )

        queryset = FlightPlan.objects.filter(departure_region__isnull=False)
        if date_from and date_to:
            queryset = queryset.filter(planned_date__range=[date_from, date_to])
        elif date_from:
            queryset = queryset.filter(planned_date__gte=date_from)
        elif date_to:
            queryset = queryset.filter(planned_date__lte=date_to)

        regions_with_flights_in_period = queryset.values(
            "departure_region__code", "departure_region__name"
        ).annotate(
            flight_days_count=Count("planned_date", distinct=True),
            total_flights=Count("id"),
        )

        period_stats_dict = {
            stat["departure_region__code"]: stat
            for stat in regions_with_flights_in_period
        }

        zero_days_stats = []

        for region in all_regions_with_flights:
            region_id = region["departure_region__id"]
            region_code = region["departure_region__code"]
            region_name = region["departure_region__name"]

            if region_code in period_stats_dict:
                stat = period_stats_dict[region_code]
                flight_days = stat["flight_days_count"]
                zero_days = total_days - flight_days
                total_flights = stat["total_flights"]
            else:
                flight_days = 0
                zero_days = total_days
                total_flights = 0

            zero_days_stats.append(
                {
                    "region_id": region_id,
                    "region_code": region_code,
                    "region_name": region_name,
                    "total_days_analyzed": total_days,
                    "flight_days": flight_days,
                    "zero_flight_days": zero_days,
                    "zero_days_percentage": round((zero_days / total_days) * 100, 2),
                    "total_flights": total_flights,
                    "flights_per_active_day": round(
                        total_flights / max(flight_days, 1), 2
                    ),
                }
            )

        zero_days_stats.sort(key=lambda x: x["zero_flight_days"], reverse=True)

        return zero_days_stats

    @classmethod
    def get_comprehensive_analytics(
        cls, date_from: date = None, date_to: date = None
    ) -> dict:
        """
        Комплексная аналитика: все метрики в одном ответе.
        """
        if not date_from and not date_to:
            first_flight = FlightPlan.objects.order_by("planned_date").first()
            last_flight = FlightPlan.objects.order_by("-planned_date").first()
            if first_flight and last_flight:
                date_from = first_flight.planned_date
                date_to = last_flight.planned_date
            else:
                date_from = date.today() - timedelta(days=30)
                date_to = date.today()
        elif not date_from:
            date_from = date.today() - timedelta(days=30)
        elif not date_to:
            date_to = date.today()

        logger.info(f"Расчет комплексной аналитики за период {date_from} - {date_to}")

        try:
            return {
                "analysis_period": {
                    "date_from": date_from.isoformat(),
                    "date_to": date_to.isoformat(),
                    "total_days": (date_to - date_from).days + 1,
                },
                "peak_load": cls.get_peak_load_statistics(date_from, date_to),
                "daily_dynamics": cls.get_daily_dynamics(date_from, date_to),
                "growth_decline": cls.get_growth_decline_statistics(
                    date_to.replace(day=1)
                ),
                "flight_density": cls.get_flight_density_by_regions(date_from, date_to),
                "daily_activity": cls.get_daily_activity_distribution(
                    date_from, date_to
                ),
                "zero_flight_days": cls.get_zero_flight_days_by_regions(
                    date_from, date_to
                )[
                    :20
                ],  # Топ-20
            }
        except Exception as e:
            logger.error(f"Ошибка расчета комплексной аналитики: {e}")
            raise

    @classmethod
    def get_regional_comparison(
        cls, region_codes: list[str], date_from: date = None, date_to: date = None
    ) -> dict:
        """
        Сравнительный анализ регионов по всем метрикам.
        """
        if not date_from and not date_to:
            first_flight = FlightPlan.objects.order_by("planned_date").first()
            last_flight = FlightPlan.objects.order_by("-planned_date").first()
            if first_flight and last_flight:
                date_from = first_flight.planned_date
                date_to = last_flight.planned_date
            else:
                date_from = date.today() - timedelta(days=30)
                date_to = date.today()
        elif not date_from:
            date_from = date.today() - timedelta(days=30)
        elif not date_to:
            date_to = date.today()

        comparison_data = {}

        for region_code in region_codes:
            try:
                region_flights = FlightPlan.objects.filter(
                    departure_region__code=region_code,
                )
                if date_from and date_to:
                    region_flights = region_flights.filter(
                        planned_date__range=[date_from, date_to]
                    )
                elif date_from:
                    region_flights = region_flights.filter(planned_date__gte=date_from)
                elif date_to:
                    region_flights = region_flights.filter(planned_date__lte=date_to)

                total_flights = region_flights.count()

                if total_flights == 0:
                    region_obj = RussianRegion.objects.get(code=region_code)
                    comparison_data[region_code] = {
                        "region_id": region_obj.id,
                        "region_name": region_obj.name,
                        "total_flights": 0,
                        "all_metrics_zero": True,
                    }
                    continue

                try:
                    region_obj = RussianRegion.objects.filter(code=region_code).first()
                    if region_obj and region_obj.area and region_obj.area.strip():
                        region_area = float(region_obj.area.replace(",", "."))
                    else:
                        region_area = 1
                except (ValueError, AttributeError):
                    region_area = 1

                density = (total_flights / region_area) * 1000

                flight_days = region_flights.values("planned_date").distinct().count()
                total_days = (
                    (date_to - date_from).days + 1 if date_from and date_to else 1
                )
                zero_days = total_days - flight_days

                avg_duration = region_flights.aggregate(
                    avg_duration=Avg("planned_duration")
                )["avg_duration"]

                region_obj = RussianRegion.objects.get(code=region_code)
                comparison_data[region_code] = {
                    "region_id": region_obj.id,
                    "region_name": region_obj.name,
                    "total_flights": total_flights,
                    "density_per_1000km2": round(density),
                    "zero_flight_days": zero_days,
                    "flight_days": flight_days,
                    "avg_duration_minutes": (
                        int(avg_duration.total_seconds() / 60) if avg_duration else 0
                    ),
                    "flights_per_day": round(total_flights / max(flight_days, 1), 2),
                }

            except RussianRegion.DoesNotExist:
                comparison_data[region_code] = {"error": "Регион не найден"}
            except Exception as e:
                comparison_data[region_code] = {"error": str(e)}

        return {
            "analysis_period": {
                "date_from": date_from.isoformat(),
                "date_to": date_to.isoformat(),
            },
            "regions_comparison": comparison_data,
        }

    @classmethod
    def get_regional_growth_trends(cls, current_month: date = None) -> dict:
        """
        Анализ роста/падения полетов по регионам за месяц.
        Для каждого региона отдельно рассчитывается процент изменения.
        """
        if not current_month:
            current_month = date.today().replace(day=1)

        if current_month.month == 1:
            previous_month = current_month.replace(
                year=current_month.year - 1, month=12
            )
        else:
            previous_month = current_month.replace(month=current_month.month - 1)

        current_month_end = current_month.replace(
            day=monthrange(current_month.year, current_month.month)[1]
        )
        previous_month_end = previous_month.replace(
            day=monthrange(previous_month.year, previous_month.month)[1]
        )

        all_regions = (
            FlightPlan.objects.filter(
                departure_region__isnull=False,
                planned_date__range=[previous_month, current_month_end],
            )
            .values(
                "departure_region__id",
                "departure_region__code",
                "departure_region__name",
            )
            .distinct("departure_region__code")
            .order_by("departure_region__code")
        )

        current_month_stats = (
            FlightPlan.objects.filter(
                planned_date__range=[current_month, current_month_end],
                departure_region__isnull=False,
            )
            .values("departure_region__code", "departure_region__name")
            .annotate(flights_count=Count("id"))
        )

        current_stats_dict = {
            stat["departure_region__code"]: stat["flights_count"]
            for stat in current_month_stats
        }

        previous_month_stats = (
            FlightPlan.objects.filter(
                planned_date__range=[previous_month, previous_month_end],
                departure_region__isnull=False,
            )
            .values("departure_region__code", "departure_region__name")
            .annotate(flights_count=Count("id"))
        )

        previous_stats_dict = {
            stat["departure_region__code"]: stat["flights_count"]
            for stat in previous_month_stats
        }

        regional_growth = []
        total_current_flights = 0
        total_previous_flights = 0

        for region in all_regions:
            region_id = region["departure_region__id"]
            region_code = region["departure_region__code"]
            region_name = region["departure_region__name"]

            current_flights = current_stats_dict.get(region_code, 0)
            previous_flights = previous_stats_dict.get(region_code, 0)

            total_current_flights += current_flights
            total_previous_flights += previous_flights

            if previous_flights == 0:
                growth_rate = 100.0 if current_flights > 0 else 0.0
                trend = "новая активность" if current_flights > 0 else "без изменений"
            else:
                growth_rate = (
                    (current_flights - previous_flights) / previous_flights
                ) * 100
                if growth_rate > 0:
                    trend = "рост"
                elif growth_rate < 0:
                    trend = "падение"
                else:
                    trend = "стабильно"

            regional_growth.append(
                {
                    "region_id": region_id,
                    "region_code": region_code,
                    "region_name": region_name,
                    "current_month": {
                        "flights_count": current_flights,
                        "date": current_month.isoformat(),
                    },
                    "previous_month": {
                        "flights_count": previous_flights,
                        "date": previous_month.isoformat(),
                    },
                    "growth_rate_percent": round(growth_rate, 2),
                    "absolute_change": current_flights - previous_flights,
                    "trend": trend,
                }
            )

        regional_growth.sort(key=lambda x: x["growth_rate_percent"], reverse=True)

        overall_growth_rate = 0
        if total_previous_flights > 0:
            overall_growth_rate = (
                (total_current_flights - total_previous_flights)
                / total_previous_flights
            ) * 100

        growth_regions = [r for r in regional_growth if r["growth_rate_percent"] > 0]
        decline_regions = [r for r in regional_growth if r["growth_rate_percent"] < 0]
        stable_regions = [r for r in regional_growth if r["growth_rate_percent"] == 0]

        return {
            "analysis_period": {
                "current_month": current_month.isoformat(),
                "previous_month": previous_month.isoformat(),
            },
            "overall_statistics": {
                "total_regions_analyzed": len(regional_growth),
                "total_current_flights": total_current_flights,
                "total_previous_flights": total_previous_flights,
                "overall_growth_rate_percent": round(overall_growth_rate, 2),
                "overall_absolute_change": total_current_flights
                - total_previous_flights,
                "overall_trend": (
                    "рост"
                    if overall_growth_rate > 0
                    else "падение" if overall_growth_rate < 0 else "стабильно"
                ),
            },
            "trend_summary": {
                "growing_regions": len(growth_regions),
                "declining_regions": len(decline_regions),
                "stable_regions": len(stable_regions),
                "top_growth_region": growth_regions[0] if growth_regions else None,
                "top_decline_region": decline_regions[-1] if decline_regions else None,
            },
            "regional_details": regional_growth,
            "top_growing_regions": growth_regions[:10],
            "top_declining_regions": sorted(
                decline_regions, key=lambda x: x["growth_rate_percent"]
            )[:10],
        }
