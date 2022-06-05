import json

from django.test import TestCase
from django.urls import resolve, reverse
from django.contrib.auth import get_user_model
from django.forms.models import model_to_dict

from ..views import CreateSchemaView
from ..models import Schema


class GenericCBVTestsMixin:
    @classmethod
    def setUpTestData(cls):
        cls.user = get_user_model().objects.create_user(  # type: ignore
            username="testuser", password="12345"
        )

    def test_url_resolves_to_view(self):
        self.assertIs(resolve(self.VIEW_URL).func.view_class, self.VIEW_CLASS)

    def test_call_view_deny_anonymous(self):
        response = self.client.get(self.VIEW_URL, follow=True)
        self.assertRedirects(response, reverse("users:login") + "?next=" + self.VIEW_URL)  # type: ignore

        response = self.client.post(self.VIEW_URL, follow=True)
        self.assertRedirects(response, reverse("users:login") + "?next=" + self.VIEW_URL)  # type: ignore

    def test_call_view_allows_registered(self):
        self.client.force_login(self.user)
        response = self.client.get(self.VIEW_URL)
        self.assertEqual(response.status_code, 200)

    def test_view_uses_correct_template(self):
        self.client.force_login(self.user)
        response = self.client.get(self.VIEW_URL)
        self.assertTemplateUsed(response, self.VIEW_TEMPLATE)  # type: ignore


class TestCreateSchemaView(GenericCBVTestsMixin, TestCase):
    VIEW_URL = reverse("schema:create")
    VIEW_CLASS = CreateSchemaView
    VIEW_TEMPLATE = "schema/edit.html"

    def test_successfully_creates_a_schema(self):
        self.client.force_login(self.user)

        input_data = {
            "name": "New",
            "column_separator": ",",
            "quotechar": '"',
            "fields": [
                {
                    "name": "Name",
                    "order": 1,
                    "f_type": "name",
                    "f_params": {},
                },
                {
                    "name": "Age",
                    "order": 2,
                    "f_type": "random_int",
                    "f_params": {"min": 5, "max": 65},
                },
            ],
        }
        self.assertEqual(0, Schema.objects.count())
        # note that fields is a JSON string
        response = self.client.post(
            self.VIEW_URL,
            data=input_data | {"fields": json.dumps(input_data["fields"])},
        )

        self.assertRedirects(response, reverse("schema:list"))  # type: ignore
        self.assertEqual(1, Schema.objects.count())
        schema_data = model_to_dict(Schema.objects.first())  # type: ignore
        self.assertDictEqual(schema_data, schema_data | input_data)

    def test_accept_incorrect_input_and_render_errors(self):
        self.client.force_login(self.user)
        # incorrect min-max range and a name duplicate
        input_data = {
            "name": "New",
            "column_separator": ",",
            "quotechar": '"',
            "fields": [
                {
                    "name": "Name",
                    "order": 1,
                    "f_type": "name",
                    "f_params": {},
                },
                {
                    "name": "Name",
                    "order": 2,
                    "f_type": "random_int",
                    "f_params": {"min": 55, "max": -65},
                },
            ],
        }
        self.assertEqual(0, Schema.objects.count())
        # note that fields is a JSON string
        response = self.client.post(
            self.VIEW_URL,
            data=input_data | {"fields": json.dumps(input_data["fields"])},
        )
        self.assertTrue(response.status_code, 200)

        self.assertEqual(len(response.context["form"].errors["fields"]), 2, response.context["form"].errors)  # type: ignore
        self.assertIn(
            "Invalid fields.", response.context["form"].errors["fields"][0]
        )
        self.assertIn(
            "Duplicate field names: Name",
            response.context["form"].errors["fields"][1],
        )
        for expected_error in [
            "Invalid fields",
            "Duplicate field names: Name",
        ]:
            self.assertContains(response, expected_error)

        rand_int_form = response.context["form"].field_forms[1]
        self.assertTrue(len(rand_int_form.errors), 4)
        for expected_error in [
            "Min value must be less than max value",
            "Max value must be greater than min value",
            "Min must be less than max",
            "Duplicate field name",
        ]:
            self.assertContains(response, expected_error)
