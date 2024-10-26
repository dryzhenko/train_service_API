from django.db import transaction
from rest_framework import serializers
from rest_framework.exceptions import ValidationError

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


class CrewSerializer(serializers.ModelSerializer):
    class Meta:
        model = Crew
        fields = ("id", "first_name", "last_name")


class StationSerializer(serializers.ModelSerializer):
    class Meta:
        model = Station
        fields = ("id", "name", "latitude", "longitude")


class StationListSerializer(StationSerializer):
    class Meta:
        model = Station
        fields = ("name",)


class RouteSerializer(serializers.ModelSerializer):
    class Meta:
        model = Route
        fields = ("id", "source", "destination", "distance")


class RouteListSerializer(RouteSerializer):
    source = serializers.SlugRelatedField(
        read_only=True,
        slug_field="name",
    )
    destination = serializers.SlugRelatedField(
        read_only=True,
        slug_field="name",
    )


class RouteRetrieveSerializer(RouteSerializer):
    source = StationSerializer()
    destination = StationSerializer()


class TrainTypeSerializer(serializers.ModelSerializer):
    class Meta:
        model = TrainType
        fields = ("id", "name")


class TrainSerializer(serializers.ModelSerializer):
    class Meta:
        model = Train
        fields = ("id", "name", "cargo_num", "place_in_cargo", "seats", "crew", "train_type")


class TrainImageSerializer(TrainSerializer):
    class Meta:
        model = Train
        fields = ("id", "image")


class TrainListSerializer(TrainSerializer):
    crew = serializers.SlugRelatedField(
        many=True,
        read_only=True,
        slug_field="full_name"
    )
    train_type = serializers.SlugRelatedField(
        read_only=True,
        slug_field="name"
    )


class TrainRetrieveSerializer(TrainSerializer):
    crew = CrewSerializer(many=True, read_only=True)
    train_type = TrainTypeSerializer()


class TicketSerializer(serializers.ModelSerializer):
    class Meta:
        model = Ticket
        fields = ("id", "cargo", "seat", "journey", "order")

    def validate(self, attrs):
        data = super(TicketSerializer, self).validate(attrs=attrs)
        Ticket.validate_ticket(
            attrs["seat"],
            attrs["journey"].train.seats,
            ValidationError
        )

        return data


class JourneyListSerializer(serializers.ModelSerializer):
    route_distance = serializers.IntegerField(source="route.distance", read_only=True)
    train_name = serializers.CharField(source="train.name", read_only=True)
    train_type = serializers.CharField(source="train.train_type.name", read_only=True)
    tickets_available = serializers.IntegerField(read_only=True)

    class Meta:
        model = Journey
        fields = ("id", "route_distance", "train_name", "train_type", "departure_time", "tickets_available")


class TicketListSerializer(TicketSerializer):
    journey = JourneyListSerializer(many=False, read_only=True)


class OrderSerializer(serializers.ModelSerializer):
    tickets = TicketSerializer(many=True, read_only=False, allow_null=False)

    class Meta:
        model = Order
        fields = ("id", "tickets", "created_at")

    def create(self, validated_data):
        with transaction.atomic():
            tickets_data = validated_data.pop("tickets")
            order = Order.objects.create(**validated_data)

            for ticket_data in tickets_data:
                Ticket.objects.create(order=order, **ticket_data)

            return order


class OrderListSerializer(OrderSerializer):
    tickets = TicketListSerializer(many=True, read_only=True)


class JourneySerializer(serializers.ModelSerializer):
    class Meta:
        model = Journey
        fields = ("id", "route", "train", "departure_time", "arrival_time")


class JourneyRetrieveSerializer(JourneySerializer):
    route = RouteRetrieveSerializer()
    train = TrainRetrieveSerializer()

    taken_seats = serializers.SlugRelatedField(
        many=True,
        read_only=True,
        slug_field="seat",
        source="ticket_set"
    )

    class Meta:
        model = Journey
        fields = ("id", "route", "train", "departure_time", "arrival_time", "taken_seats")
