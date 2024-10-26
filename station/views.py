from django.db.models import Count, F
from drf_spectacular.utils import extend_schema, OpenApiParameter
from rest_framework import viewsets, status
from rest_framework.decorators import action
from rest_framework.pagination import PageNumberPagination
from rest_framework.permissions import IsAdminUser
from rest_framework.response import Response

from station.permissions import IsAdminOrIfAuthenticatedReadOnly


from station.models import (
    Crew,
    Station,
    Route,
    TrainType,
    Train,
    Order,
    Journey,
    Ticket
)

from station.serializers import (
    CrewSerializer,
    StationSerializer,
    RouteSerializer,
    TrainTypeSerializer,
    TrainSerializer,
    OrderSerializer,
    JourneySerializer,
    TicketSerializer,
    JourneyListSerializer,
    TrainListSerializer,
    TrainRetrieveSerializer,
    RouteListSerializer,
    RouteRetrieveSerializer,
    JourneyRetrieveSerializer, OrderListSerializer, TrainImageSerializer,
)


class CrewViewSet(viewsets.ModelViewSet):
    queryset = Crew.objects.all()
    serializer_class = CrewSerializer


class StationViewSet(viewsets.ModelViewSet):
    queryset = Station.objects.all()
    serializer_class = StationSerializer


class RouteViewSet(viewsets.ModelViewSet):
    queryset = Route.objects.select_related("source", "destination")

    def get_serializer_class(self):
        if self.action == 'list':
            return RouteListSerializer
        elif self.action == 'retrieve':
            return RouteRetrieveSerializer

        return RouteSerializer

    def get_queryset(self):
        queryset = self.queryset
        if self.action == 'list':
            queryset = queryset.select_related("source", "destination")
        elif self.action == 'retrieve':
            queryset = queryset.select_related("source", "destination")

        return queryset


class TrainTypeViewSet(viewsets.ModelViewSet):
    queryset = TrainType.objects.all()
    serializer_class = TrainTypeSerializer


class TrainViewSet(viewsets.ModelViewSet):
    queryset = Train.objects.prefetch_related("crew")
    http_method_names = ['get', 'post', 'patch']

    @staticmethod
    def _params_to_ints(qs):
        """Converts a list of string IDs to a list of integers"""
        return [int(str_id) for str_id in qs.split(",")]

    def get_serializer_class(self):
        if self.action == 'list':
            return TrainListSerializer
        elif self.action == 'retrieve':
            return TrainRetrieveSerializer
        elif self.action == "upload_image":
            return TrainImageSerializer

        return TrainSerializer

    def get_queryset(self):
        queryset = self.queryset

        crew = self.request.query_params.get("crew")
        train_type = self.request.query_params.get("train_type")

        if crew:
            crew = self._params_to_ints(crew)
            queryset = queryset.filter(crew__in=crew)

        if train_type:
            train_type = self._params_to_ints(train_type)
            queryset = queryset.filter(train_type_id__in=train_type)

        if self.action == 'list':
            queryset = queryset.prefetch_related("crew")
        elif self.action == 'retrieve':
            queryset = queryset.prefetch_related("crew")

        return queryset.distinct()


    @action(
        methods=["POST"],
        detail=True,
        url_path="upload-image",
        permission_classes=[IsAdminUser],
    )
    def upload_image(self, request, pk=None):
        """Endpoint for uploading image to specific movie"""
        train = self.get_object()
        serializer = self.get_serializer(train, data=request.data)

        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data, status=status.HTTP_200_OK)

        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    @extend_schema(
        parameters=[
            OpenApiParameter(
                "crew",
                type={"type": "array", "items": {"type": "string"}},
                description="Filter by crew",
            ),
            OpenApiParameter(
                "train_type",
                type={"type": "array", "items": {"type": "string"}},
                description="Filter by genres",
            )
        ]
    )
    def list(self, request, *args, **kwargs):
        return super().list(request, *args, **kwargs)


class OrderSetPagination(PageNumberPagination):
    page_size = 5
    page_size_query_param = "page_size"
    max_page_size = 100


class OrderViewSet(viewsets.ModelViewSet):
    queryset = Order.objects.all()
    serializer_class = OrderSerializer
    pagination_class = OrderSetPagination

    def get_queryset(self):
        queryset = self.queryset.filter(user=self.request.user)

        if self.action == "list":
            queryset = queryset.prefetch_related("tickets__journey__train")

        return queryset

    def perform_create(self, serializer):
        serializer.save()

    def get_serializer_class(self):
        if self.action == "list":
            return OrderListSerializer

        return OrderSerializer


class JourneyViewSet(viewsets.ModelViewSet):
    queryset = Journey.objects.select_related("train", "route")

    def get_serializer_class(self):
        if self.action == 'list':
            return JourneyListSerializer
        elif self.action == 'retrieve':
            return JourneyRetrieveSerializer

        return JourneySerializer

    def get_queryset(self):
        queryset = self.queryset
        if self.action == 'list':
            queryset = (
                queryset.select_related("train").annotate(tickets_available=F("train__seats") - Count("ticket"))
            ).order_by("id")
            return queryset.select_related("train", "route")
        elif self.action == 'retrieve':
            return queryset.select_related("train", "route")

        return queryset


class TicketViewSet(viewsets.ModelViewSet):
    queryset = Ticket.objects.all()
    serializer_class = TicketSerializer
