from django.urls import path, include
from rest_framework import routers
from station.views import (
    CrewViewSet,
    StationViewSet,
    RouteViewSet,
    TrainTypeViewSet,
    TrainViewSet,
    OrderViewSet,
    JourneyViewSet,
    TicketViewSet,
)

router = routers.DefaultRouter()
router.register("crew", CrewViewSet, basename="crew")
router.register("station", StationViewSet, basename="station")
router.register("route", RouteViewSet, basename="route")
router.register("train_type", TrainTypeViewSet, basename="train_type")
router.register("train", TrainViewSet, basename="train")
router.register("order", OrderViewSet, basename="order")
router.register("journey", JourneyViewSet, basename="journey")
router.register("ticket", TicketViewSet, basename="ticket")
urlpatterns = [path("", include(router.urls))]

app_name = "journey"
