from types import SimpleNamespace

from django.test import TestCase
from django.contrib.auth import get_user_model
from django.forms.models import model_to_dict

from ...rest_api.serializers import SchemaSerializer
from ...models import NameColumn, RandomIntColumn


class TestSchemaSerializer(TestCase):
    @classmethod
    def setUpTestData(cls):
        cls.user = get_user_model().objects.create_user(
            username="testuser", password="12345"
        )

    def test_serialize_normal(self):
        schema_data = {
            "name": "People",
            "column_separator": ";",
            "quotechar": "!",
            "columns": [
                {
                    "type": "name",
                    "params": {"name": "Full name"},
                },
                {
                    "type": "random_int",
                    "params": {"name": "Age", "order": 1, "min": 1, "max": 5},
                },
            ],
        }
        serializer = SchemaSerializer(data=schema_data)
        self.assertTrue(serializer.is_valid(), serializer.errors)
        validated_data = serializer.validated_data

        name_col = NameColumn(**{"name": "Full name"})
        rand_int_col = RandomIntColumn(
            **{"name": "Age", "order": 1, "min": 1, "max": 5}
        )
        self.assertDictEqual(
            model_to_dict(name_col),
            model_to_dict(validated_data["columns"][0]),
        )
        self.assertDictEqual(
            model_to_dict(rand_int_col),
            model_to_dict(validated_data["columns"][1]),
        )

    def test_serialize_invalid_col_type(self):
        schema_data = {
            "name": "People",
            "column_separator": ";",
            "quotechar": "!",
            "columns": [
                {
                    "type": "non_existent_type",
                    "params": {"name": "Full name"},
                },
            ],
        }

        serializer = SchemaSerializer(data=schema_data)
        self.assertFalse(serializer.is_valid())
        # TODO: add an assertion for specific error messages

    def test_serialize_nonexistent_col_param(self):
        schema_data = {
            "name": "People",
            "column_separator": ";",
            "quotechar": "!",
            "columns": [
                {
                    "type": "random_int",
                    "params": {"name": "Full name", "nonexistent_param": 1337},
                },
            ],
        }

        serializer = SchemaSerializer(data=schema_data)
        self.assertFalse(serializer.is_valid())
        # TODO: add an assertion for specific error messages

    def test_serialize_invalid_col_param(self):
        schema_data = {
            "name": "People",
            "column_separator": ";",
            "quotechar": "!",
            "columns": [
                {
                    "type": "random_int",
                    "params": {"name": "Full name", "min": 1337, "max": 322},
                },
            ],
        }
        serializer = SchemaSerializer(data=schema_data)
        self.assertFalse(serializer.is_valid())
        # TODO: add an assertion for specific error messages
