import os
import uuid

from django.db import models
from django.conf import settings
from django.db.models import UniqueConstraint
from django.utils.text import slugify
from rest_framework.exceptions import ValidationError


class Crew(models.Model):
    first_name = models.CharField(max_length=50)
    last_name = models.CharField(max_length=50)

    def __str__(self):
        return self.first_name + " " + self.last_name

    @property
    def full_name(self):
        return f"{self.first_name} {self.last_name}"


class Station(models.Model):
    name = models.CharField(max_length=100)
    latitude = models.FloatField()
    longitude = models.FloatField()

    def __str__(self):
        return self.name


class Route(models.Model):
    source = models.ForeignKey(
        Station,
        on_delete=models.CASCADE,
        related_name="source"
    )
    destination = models.ForeignKey(
        Station,
        on_delete=models.CASCADE,
        related_name="destination"
    )
    distance = models.IntegerField()

    def __str__(self):
        return (
            f"Source: {self.source}, "
            f"Destination: {self.destination}, "
            f"Distance: {self.distance}"
        )


class TrainType(models.Model):
    name = models.CharField(max_length=100)

    def __str__(self):
        return self.name


def movie_image_file_path(instance, filename):
    _, extension = os.path.splitext(filename)
    filename = f"{slugify(instance.name)}-{uuid.uuid4()}{extension}"

    return os.path.join("uploads/trains/", filename)


class Train(models.Model):
    name = models.CharField(max_length=100)
    cargo_num = models.IntegerField()
    place_in_cargo = models.IntegerField()
    seats = models.IntegerField()
    crew = models.ManyToManyField(Crew, related_name="trains")
    train_type = models.ForeignKey(
        TrainType, on_delete=models.CASCADE, related_name="trains"
    )
    image = models.ImageField(
        null=True,
        upload_to=movie_image_file_path
    )

    def __str__(self):
        return (
            f"Name: {self.name}, "
            f"Num of cargo: {self.cargo_num}, "
            f"Place in cargo: {self.place_in_cargo}, "
            f"Seats: {self.seats}, "
            f"Crew: {self.crew}"
            f"Train type: {self.train_type}"
        )


class Order(models.Model):
    created_at = models.DateTimeField(auto_now_add=True)
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE
    )

    def __str__(self):
        return str(self.created_at)

    class Meta:
        ordering = ["-created_at"]


class Journey(models.Model):
    route = models.ForeignKey(
        Route,
        on_delete=models.CASCADE,
        related_name="journeys"
    )
    train = models.ForeignKey(
        Train,
        on_delete=models.CASCADE,
        related_name="journeys"
    )
    departure_time = models.DateTimeField()
    arrival_time = models.DateTimeField()

    class Meta:
        ordering = ["-departure_time"]

    def __str__(self):
        return (
            f"Route: {self.route}, "
            f"Train {self.train}, "
            f"Departure time: {self.departure_time}, "
            f"Arrival time: {self.arrival_time}"
        )


class Ticket(models.Model):
    cargo = models.IntegerField()
    seat = models.IntegerField()
    journey = models.ForeignKey(
        Journey,
        on_delete=models.CASCADE
    )
    order = models.ForeignKey(
        Order,
        on_delete=models.CASCADE,
        related_name="tickets"
    )

    class Meta:
        unique_together = ["journey", "order"]
        ordering = ["seat"]

    @staticmethod
    def validate_ticket(cargo, seat, train, error_to_raise):
        for ticket_attr_value, ticket_attr_name, train_attr_name in [
            (cargo, "cargo", "cargo_num"),
            (seat, "seat", "seats"),
        ]:
            count_attrs = getattr(train, train_attr_name)
            if not (1 <= ticket_attr_value <= count_attrs):
                raise error_to_raise(
                    {
                        ticket_attr_name: f"{ticket_attr_name.capitalize()} "
                        f"must be in range: (1, {count_attrs})."
                    }
                )

    def clean(self):
        train = self.journey.train
        Ticket.validate_ticket(
            cargo=self.cargo,
            seat=self.seat,
            train=train,
            error_to_raise=ValidationError,
        )

    def save(
        self,
        force_insert=False,
        force_update=False,
        using=None,
        update_fields=None,
        **kwargs,
    ):
        self.full_clean()
        return super(Ticket, self).save(
            force_insert, force_update, using, update_fields
        )
