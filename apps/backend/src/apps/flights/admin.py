"""
Django Admin конфигурация для приложения flights.
"""

from django.contrib import admin
from django.contrib.gis.admin import GISModelAdmin
from django.shortcuts import redirect, render
from django.urls import path
from django.utils.translation import gettext_lazy as _

from .forms import ExcelUploadForm
from .models import (
    DroneType,
    FlightPlan,
    RussianRegion,
)
from .services import FlightDataParser


@admin.register(RussianRegion)
class RussianRegionAdmin(GISModelAdmin):
    """Админ интерфейс для управления регионами РФ."""

    list_display = ["name", "code", "status", "utc", "timezone", "created"]
    list_filter = ["created", "status", "utc"]
    search_fields = ["name", "code", "okato"]
    readonly_fields = ["created", "modified"]

    fieldsets = (
        (_("Основная информация"), {"fields": ("name", "code", "okato", "status")}),
        (_("Часовой пояс"), {"fields": ("utc", "timezone")}),
        (_("Геометрия"), {"fields": ("geometry",)}),
        (
            _("Системная информация"),
            {"fields": ("created", "modified"), "classes": ("collapse",)},
        ),
    )


@admin.register(DroneType)
class DroneTypeAdmin(admin.ModelAdmin):
    """Админ интерфейс для управления типами БАС."""

    list_display = ["code", "name", "created"]
    list_filter = ["created"]
    search_fields = ["code", "name"]
    readonly_fields = ["created", "modified"]

    fieldsets = (
        (_("Основная информация"), {"fields": ("code", "name", "description")}),
        (
            _("Системная информация"),
            {"fields": ("created", "modified"), "classes": ("collapse",)},
        ),
    )


@admin.register(FlightPlan)
class FlightPlanAdmin(GISModelAdmin):
    """Админ интерфейс для управления планами полетов."""

    list_display = [
        "sid",
        "flight_id",
        "planned_date",
        "planned_departure_time",
        "operator",
        "drone_type",
        "departure_region",
        "created",
    ]

    list_filter = [
        "planned_date",
        "drone_type",
        "departure_region",
        "destination_region",
        "created",
    ]

    search_fields = ["flight_id", "sid", "reg_number", "operator__name", "purpose"]

    readonly_fields = ["created", "modified"]

    raw_id_fields = ["operator", "flight_zone"]

    date_hierarchy = "planned_date"

    fieldsets = (
        (_("Идентификация"), {"fields": ("flight_id", "sid", "reg_number")}),
        (
            _("Временные данные"),
            {"fields": ("planned_date", "planned_departure_time", "planned_duration")},
        ),
        (_("Высотные характеристики"), {"fields": ("min_altitude", "max_altitude")}),
        (
            _("Геопространственные данные"),
            {
                "fields": (
                    "departure_point",
                    "destination_point",
                    "departure_region",
                    "destination_region",
                )
            },
        ),
        (_("Связанные объекты"), {"fields": ("operator", "drone_type", "flight_zone")}),
        (
            _("Дополнительная информация"),
            {"fields": ("purpose", "special_conditions"), "classes": ("collapse",)},
        ),
        (
            _("Служебные данные"),
            {"fields": ("raw_data", "created", "modified"), "classes": ("collapse",)},
        ),
    )

    def get_urls(self):
        urls = super().get_urls()
        custom_urls = [
            path(
                "upload-excel/",
                self.admin_site.admin_view(self.upload_excel_view),
                name="flights_flightplan_upload_excel",
            ),
        ]
        return custom_urls + urls

    def upload_excel_view(self, request):
        if request.method == "POST":
            form = ExcelUploadForm(request.POST, request.FILES)
            if form.is_valid():
                try:
                    parser = FlightDataParser()
                    results = parser.parse_excel_file(request.FILES["excel_file"])

                    self.message_user(
                        request,
                        _(
                            f"Успешно обработано {results['processed']} записей. "
                            f"Ошибок: {results['errors']}. "
                            f"Создано планов полетов: {results['created']}."
                        ),
                    )

                    return redirect("admin:flights_flightplan_changelist")

                except Exception as e:
                    self.message_user(
                        request,
                        _(f"Ошибка при обработке файла: {str(e)}"),
                        level="ERROR",
                    )
        else:
            form = ExcelUploadForm()

        context = {
            "form": form,
            "title": _("Загрузка планов полетов из Excel"),
            "opts": self.model._meta,
        }

        return render(request, "admin/flights/flight_plan_upload.html", context)

    def changelist_view(self, request, extra_context=None):
        extra_context = extra_context or {}
        extra_context["upload_excel_url"] = "admin:flights_flightplan_upload_excel"
        return super().changelist_view(request, extra_context)


class FlightsAdminConfig:
    """Конфигурация для группировки моделей в админке."""

    @staticmethod
    def customize_admin_interface():
        pass
