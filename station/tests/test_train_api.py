import tempfile
import os

from PIL import Image
from django.contrib.auth import get_user_model
from django.test import TestCase
from django.urls import reverse

from rest_framework.test import APIClient
from rest_framework import status

from station.models import Train, Journey, Route, TrainType, Crew
from station.serializers import TrainListSerializer, TrainRetrieveSerializer

TRAIN_URL = reverse("journey:train-list")
JOURNEY_URL = reverse("journey:journey-list")


def sample_train_type(name="Freight"):
    return TrainType.objects.create(name=name)


def sample_train(**params):
    train_type = TrainType.objects.create(name="Freight")
    defaults = {
        "name": "Express",
        "cargo_num": 10,
        "place_in_cargo": 5,
        "seats": 100,
        "train_type": train_type,
    }
    defaults.update(params)
    return Train.objects.create(**defaults)


def sample_journey(**params):
    route = Route.objects.create(source_id=1, destination_id=2, distance=100)
    defaults = {
        "route": route,
        "train": None,
        "departure_time": "2022-06-02 14:00:00",
        "arrival_time": "2022-06-02 18:00:00",
    }
    defaults.update(params)
    return Journey.objects.create(**defaults)


def image_upload_url(train_id):
    """Return URL for train image upload"""
    return reverse("journey:train-upload-image", args=[train_id])


def detail_url(train_id):
    return reverse("journey:train-detail", args=[train_id])


class UnauthenticatedTrainApiTests(TestCase):
    def setUp(self):
        self.client = APIClient()

    def test_auth_required(self):
        res = self.client.get(TRAIN_URL)
        self.assertEqual(res.status_code, status.HTTP_401_UNAUTHORIZED)


class AuthenticatedTrainApiTests(TestCase):
    def setUp(self):
        self.client = APIClient()
        self.user = get_user_model().objects.create_user(
            "test@test.com",
            "testpass",
        )
        self.client.force_authenticate(self.user)

    def test_list_trains(self):
        sample_train()
        sample_train()

        res = self.client.get(TRAIN_URL)

        trains = Train.objects.order_by("id")
        serializer = TrainListSerializer(trains, many=True)

        self.assertEqual(res.status_code, status.HTTP_200_OK)
        self.assertEqual(res.data['results'], serializer.data)

    def test_retrieve_train_detail(self):
        train = sample_train()
        train_type = TrainType.objects.create(name="Freight")
        train.train_type = train_type
        train.save()

        url = detail_url(train.id)
        res = self.client.get(url)

        serializer = TrainRetrieveSerializer(train)
        self.assertEqual(res.status_code, status.HTTP_200_OK)
        self.assertEqual(res.data, serializer.data)

    def test_create_train_forbidden(self):
        payload = {
            "name": "Bullet",
            "cargo_num": 5,
            "place_in_cargo": 2,
            "seats": 200,
        }
        res = self.client.post(TRAIN_URL, payload)

        self.assertEqual(res.status_code, status.HTTP_403_FORBIDDEN)


class AdminTrainApiTests(TestCase):
    def setUp(self):
        self.client = APIClient()
        self.user = get_user_model().objects.create_user(
            "admin@gmail.com", "1qazcde3", is_staff=True
        )
        self.client.force_authenticate(self.user)

    def test_create_train(self):
        train_type = TrainType.objects.create(name="Freight")
        crew_member = Crew.objects.create(first_name="John", last_name="Doe")
        payload = {
            "name": "Express",
            "cargo_num": 10,
            "place_in_cargo": 5,
            "seats": 100,
            "train_type": train_type.id,
            "crew": [crew_member.id],
        }
        res = self.client.post(reverse("journey:train-list"), payload)

        self.assertEqual(res.status_code, status.HTTP_201_CREATED)

    def test_create_train_with_train_type(self):
        train_type = TrainType.objects.create(name="High-Speed")
        crew_member = Crew.objects.create(first_name="John", last_name="Doe")
        payload = {
            "name": "Bullet",
            "train_type": train_type.id,
            "cargo_num": 5,
            "place_in_cargo": 2,
            "seats": 200,
            "crew": [crew_member.id],
        }
        res = self.client.post(TRAIN_URL, payload)

        print(f"Response status: {res.status_code}")
        print(f"Response data: {res.data}")

        self.assertEqual(res.status_code, status.HTTP_201_CREATED)

        train = Train.objects.get(id=res.data["id"])
        self.assertEqual(train.train_type, train_type)


class TrainImageUploadTests(TestCase):
    def setUp(self):
        self.client = APIClient()
        self.user = get_user_model().objects.create_superuser(
            "admin@myproject.com", "password"
        )
        self.client.force_authenticate(self.user)
        self.train = sample_train()

    def tearDown(self):
        self.train.image.delete()

    def test_upload_image_to_train(self):
        """Test uploading an image to train"""
        url = image_upload_url(self.train.id)
        with tempfile.NamedTemporaryFile(suffix=".jpg") as ntf:
            img = Image.new("RGB", (10, 10))
            img.save(ntf, format="JPEG")
            ntf.seek(0)
            res = self.client.post(url, {"image": ntf}, format="multipart")
        self.train.refresh_from_db()

        self.assertEqual(res.status_code, status.HTTP_200_OK)
        self.assertIn("image", res.data)
        self.assertTrue(os.path.exists(self.train.image.path))

    def test_upload_image_bad_request(self):
        """Test uploading an invalid image"""
        url = image_upload_url(self.train.id)
        res = self.client.post(url, {"image": "not image"}, format="multipart")

        self.assertEqual(res.status_code, status.HTTP_400_BAD_REQUEST)

    def test_post_image_to_train_list_should_not_work(self):
        """Test that uploading image directly to train list should not work"""
        with tempfile.NamedTemporaryFile(suffix=".jpg") as ntf:
            img = Image.new("RGB", (10, 10))
            img.save(ntf, format="JPEG")
            ntf.seek(0)
            payload = {
                "name": "Bullet",
                "cargo_num": 5,
                "place_in_cargo": 2,
                "seats": 200,
                "image": ntf,
                "train_type": self.train.train_type.id,
                "crew": [],
            }
            res = self.client.post(TRAIN_URL, payload, format="multipart")

        # Змінюємо на 400, оскільки створення зображення має бути заблоковано
        self.assertEqual(res.status_code, status.HTTP_400_BAD_REQUEST)

    def test_put_train_not_allowed(self):
        """Test that PUT method is not allowed on train detail"""
        payload = {
            "name": "New Train",
            "cargo_num": 15,
            "place_in_cargo": 3,
            "seats": 120,
            "crew": [],
        }

        train = sample_train()
        url = detail_url(train.id)

        res = self.client.put(url, payload)

        self.assertEqual(res.status_code, status.HTTP_405_METHOD_NOT_ALLOWED)

    def test_delete_train_not_allowed(self):
        train = sample_train()
        url = detail_url(train.id)

        res = self.client.delete(url)

        self.assertEqual(res.status_code, status.HTTP_405_METHOD_NOT_ALLOWED)
