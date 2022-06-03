from django.contrib.auth import get_user_model
from django.contrib.auth.models import Permission
from django.forms.models import model_to_dict
from django.test import TestCase

from ...forms.main import GenerateForm, SchemaForm
from ...models import Schema


class TestSchemaFormCase(TestCase):
    @classmethod
    def setUpTestData(cls):
        cls.user = get_user_model().objects.create_user(
            username="testuser", password="12345"
        )
        cls.input_data = {
            "name": "test",
            "column_separator": ",",
            "quotechar": '"',
            "fields": [
                {"name": "Name", "order": 1, "f_type": "name", "f_params": {}},
                {
                    "name": "Age",
                    "order": 2,
                    "f_type": "random_int",
                    "f_params": {"max": 55, "min": 5},
                },
            ],
        }

    def test_simple_data_instantiation_from_data(self):
        form = SchemaForm(self.input_data)
        form.instance.user = self.user

        self.assertTrue(form.is_valid())
        self.assertEqual(len(form.field_forms), 2)

        form.instance.save()
        saved_data = model_to_dict(Schema.objects.get(name="test"))
        self.assertEqual(
            saved_data, saved_data | self.input_data
        )  # input_data is a subset of saved_data as there is no id

    def test_simple_data_instantiation_from_instance(self):
        """`instance` argument means that form initialized for rendering, so validation isn't appropriate"""
        schema = Schema.objects.create(**self.input_data, user=self.user)
        form_from_instance = SchemaForm(instance=schema)
        form_from_data = SchemaForm(self.input_data)
        form_from_data.full_clean()

        self.assertEqual(len(form_from_instance.field_forms), 2)
        self.assertEqual(
            form_from_instance.initial, form_from_data.cleaned_data
        )

    def test_validate_garbage_in_fields(self):
        input_data = self.input_data | {"fields": "complete garbage"}
        form = SchemaForm(input_data)
        self.assertFalse(form.is_valid())
        self.assertEqual(form.errors, {"fields": ["Enter a valid JSON."]})

        input_data = self.input_data | {"fields": "[]"}
        form = SchemaForm(input_data)
        self.assertFalse(form.is_valid())
        self.assertEqual(form.errors, {"fields": ["This field is required."]})

        input_data = self.input_data | {"fields": '["garbage in the list"]'}
        form = SchemaForm(input_data)
        self.assertFalse(form.is_valid())
        self.assertEqual(form.errors, {"fields": ["Error parsing fields."]})

        input_data = self.input_data | {"fields": "{}"}
        form = SchemaForm(input_data)
        self.assertFalse(form.is_valid())
        self.assertEqual(form.errors, {"fields": ["This field is required."]})

        input_data = self.input_data | {"fields": "[{}]"}
        form = SchemaForm(input_data)
        self.assertFalse(form.is_valid())
        self.assertEqual(form.errors, {"fields": ["Error parsing fields."]})

        input_data = self.input_data | {
            "fields": '[{"name": "Vasya", "order": 1}]'
        }
        form = SchemaForm(input_data)
        self.assertFalse(form.is_valid())
        self.assertEqual(form.errors, {"fields": ["Error parsing fields."]})

        input_data = self.input_data | {
            "fields": '[{"name": "Vasya", "order": 1, "f_type": "garbage"}]'
        }
        form = SchemaForm(input_data)
        self.assertFalse(form.is_valid())
        self.assertEqual(form.errors, {"fields": ["Error parsing fields."]})

        input_data = self.input_data | {
            "fields": '["garbage", \
            {"name": "Vasya", "order": 1, "f_type": "garbage"}]'
        }
        form = SchemaForm(input_data)
        self.assertFalse(form.is_valid())
        self.assertEqual(form.errors, {"fields": ["Error parsing fields."]})

        input_data = self.input_data | {
            "fields": '[{"name": "Vasya", "f_type": "name"}]'
        }
        form = SchemaForm(input_data)
        self.assertFalse(form.is_valid())
        self.assertEqual(
            form.errors,
            {
                "__all__": ["Invalid fields."],
                "fields": ["This field cannot be null."],
            },
        )
        # slightly weird error but it can't be made via normal form submission anyway
        # no need to check for further field fields error combinations as it's a job of field_forms

    def test_validate_duplicate_field_names(self):
        input_data = self.input_data.copy()
        input_data["fields"].append(
            {"name": "Name", "order": 1, "f_type": "name", "f_params": {}}
        )
        form = SchemaForm(self.input_data)
        self.assertFalse(form.is_valid())
        self.assertIn("Duplicate field names: Name", form.errors["__all__"])


class TestGenerateForm(TestCase):
    @classmethod
    def setUpTestData(cls):
        cls.user = get_user_model().objects.create_user(
            username="testuser", password="12345"
        )
        # TODO: solve the mystery: if creating cls.request here (and not overwrite in setUp), user.has_perm will fail.
        # cls.request = type(
        #     "", (), {"user": cls.user}
        # )()  # dot-accessible attribute. Do not name as `request` or magic bugs appear

    def setUp(self):
        self.request = type(
            "", (), {"user": self.user}
        )()  # dot-accessible attribute.

    def test_limited_rows_for_plebs(self):
        self.assertFalse(self.user.has_perm("schema.unlimited_generation"))

        form = GenerateForm({"num_rows": int(1e100)}, request=self.request)
        self.assertFalse(form.is_valid())

        form = GenerateForm({"num_rows": 100}, request=self.request)
        self.assertTrue(form.is_valid(), form.errors.as_json())

    def test_unlimited_rows_for_privileged_user(self):
        permission = Permission.objects.get(codename="unlimited_generation")
        self.user.user_permissions.add(permission)
        self.assertTrue(self.user.has_perm("schema.unlimited_generation"))

        form = GenerateForm({"num_rows": int(1e100)}, request=self.request)
        self.assertTrue(form.is_valid(), form.errors)
