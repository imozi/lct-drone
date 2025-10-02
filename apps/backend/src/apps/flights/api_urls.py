"""
URL маршруты для API приложения flights.
"""

from django.urls import include, path
from rest_framework.routers import DefaultRouter

from .api_viewsets import (
    DroneOperatorViewSet,
    DroneTypeViewSet,
    FlightPlanViewSet,
    RussianRegionViewSet,
    StatisticsViewSet,
)

router = DefaultRouter()

router.register(r"flight-plans", FlightPlanViewSet, basename="flightplan")
router.register(r"statistics", StatisticsViewSet, basename="statistics")
router.register(r"operators", DroneOperatorViewSet, basename="operator")
router.register(r"drone-types", DroneTypeViewSet, basename="dronetype")
router.register(r"regions", RussianRegionViewSet, basename="region")

app_name = "flights_api"
urlpatterns = [
    path("", include(router.urls)),
]
