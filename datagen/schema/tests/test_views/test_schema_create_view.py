from django.test import TestCase
from django.urls import resolve, reverse
from django.contrib.auth import get_user_model
from django.forms.models import model_to_dict

from ... import views
from ...models import BaseColumn, Schema


class TestCreateSchemaView(TestCase):
    VIEW_URL = reverse("schema:create")

    @classmethod
    def setUpTestData(cls):
        cls.user = get_user_model().objects.create_user(  # type: ignore
            username="testuser", password="12345"
        )

    @staticmethod
    def copy_form_prepared(dict_, prefix, idx: int | None = 0) -> dict:
        copy = {}
        if idx is not None:
            for key in dict_.keys():
                copy[f"{prefix}-{idx}-{key}"] = dict_[key]
        else:
            for key in dict_.keys():
                copy[f"{prefix}-{key}"] = dict_[key]

        return copy

    @staticmethod
    def get_management_form(custom_columns: dict = {}) -> dict:
        """Input data in format of `{prefix: {total: 1, initial: 0}}` or
        {prefix: {}} for a prefix with `total` of `1` and `initial` - `0`"""
        management_data = {}
        for prefix in BaseColumn.__subclasses__():
            management_data[f"{prefix.__name__}-TOTAL_FORMS"] = 0
            management_data[f"{prefix.__name__}-INITIAL_FORMS"] = 0
        for prefix, conf in custom_columns.items():
            management_data[f"{prefix}-TOTAL_FORMS"] = conf.get("total", 1)
            management_data[f"{prefix}-INITIAL_FORMS"] = conf.get("initial", 0)

        return management_data

    def test_url_resolves_to_view(self):
        self.assertIs(
            resolve(self.VIEW_URL).func.view_class, views.CreateSchemaView
        )

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
        self.assertTemplateUsed(response, "schema/edit.html")  # type: ignore

    def test_create_a_simple_schema(self):
        self.client.force_login(self.user)

        schema_data = {
            "name": "Test form",
            "column_separator": ",",
            "quotechar": '"',
        }
        name_col_data = {"name": "Name", "order": 1}
        random_int_data = {
            "name": "Age",
            "order": 2,
            "min": 5,
            "max": 55,
        }
        form_data = {
            **self.copy_form_prepared(schema_data, "Schema", idx=None),
            **self.copy_form_prepared(name_col_data, "NameColumn"),
            **self.copy_form_prepared(random_int_data, "RandomIntColumn"),
            **self.get_management_form(
                {"NameColumn": {}, "RandomIntColumn": {}}
            ),
        }

        self.assertEqual(0, Schema.objects.count())
        # note that fields is a JSON string
        response = self.client.post(self.VIEW_URL, data=form_data)

        self.assertRedirects(response, reverse("schema:list"))  # type: ignore
        self.assertEqual(1, Schema.objects.count())

        self.assertDictEqual(
            schema_data,
            model_to_dict(
                Schema.objects.first(),  # type: ignore
                fields=("name", "column_separator", "quotechar"),
            ),
        )

    def test_validate_incorrect_input_and_render_errors(self):
        self.client.force_login(self.user)
        schema_data = {
            "name": "Test form",
            "column_separator": ",",
            "quotechar": '"',
        }
        # incorrect min-max range and a name duplicate
        name_col_data = {"name": "Same Name", "order": 1}
        random_int_data = {
            "name": "Same Name",
            "order": 2,
            "min": 5,
            "max": -55,
        }

        form_data = {
            **self.copy_form_prepared(schema_data, "Schema", idx=None),
            **self.copy_form_prepared(name_col_data, "NameColumn"),
            **self.copy_form_prepared(random_int_data, "RandomIntColumn"),
            **self.get_management_form(
                {"NameColumn": {}, "RandomIntColumn": {}}
            ),
        }

        self.assertEqual(0, Schema.objects.count())
        # note that fields is a JSON string
        response = self.client.post(self.VIEW_URL, data=form_data)
        self.assertTrue(response.status_code, 200)

        self.assertListEqual(response.context["form"].non_field_errors(), ["One or more columns have errors."])  # type: ignore

        self.assertContains(response, "One or more columns have errors.")

        rand_int_form = response.context["form"].column_formsets[1][0]  # type: ignore
        self.assertTrue(len(rand_int_form.errors), 4)
        for expected_error in [
            "Min must be less than max.",
            "Max must be greater than min.",
            "Min must be less than max.",
            "This name is already used by another column.",
        ]:
            self.assertContains(response, expected_error)

    def test_validate_empty_columns(self):
        self.client.force_login(self.user)

        schema_data = {
            "name": "Test form",
            "column_separator": ",",
            "quotechar": '"',
        }

        form_data = {
            **self.copy_form_prepared(schema_data, "Schema", idx=None),
            **self.get_management_form(),
        }
        # note that fields is a JSON string
        response = self.client.post(self.VIEW_URL, data=form_data)
        self.assertTrue(response.status_code, 200)

        self.assertListEqual(response.context["form"].non_field_errors(), ["Add at least one column."])  # type: ignore
