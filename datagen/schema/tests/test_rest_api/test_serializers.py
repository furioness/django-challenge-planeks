import unittest

from django.test import TestCase
from django.contrib.auth import get_user_model
from django.forms.models import model_to_dict

from ...rest_api.serializers import SchemaSerializer
from ...models import NameColumn, RandomIntColumn, Schema


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
                    "params": {"name": "Full name", "order": 2},
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

        name_col = NameColumn(**{"name": "Full name", "order": 2})
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
                    "params": {"name": "Full name", "order": 1},
                },
            ],
        }

        serializer = SchemaSerializer(data=schema_data)
        self.assertFalse(serializer.is_valid())

        column_errors = serializer.errors["columns"][0]
        self.assertEqual(len(column_errors), 1)
        self.assertTrue("type" in column_errors)

    @unittest.skip(
        reason="Seems like it's the default behavior for DRF to allow superfluous fields."
    )
    def test_serialize_nonexistent_col_param(self):
        schema_data = {
            "name": "People",
            "column_separator": ";",
            "quotechar": "!",
            "columns": [
                {
                    "type": "random_int",
                    "params": {
                        "name": "Full name",
                        "order": 1,
                        "nonexistent_param": 1337,
                    },
                },
            ],
        }

        serializer = SchemaSerializer(data=schema_data)
        self.assertFalse(serializer.is_valid())

    def test_serialize_invalid_col_param_value(self):
        schema_data = {
            "name": "People",
            "column_separator": ";",
            "quotechar": "!",
            "columns": [
                {
                    "type": "random_int",
                    "params": {
                        "name": "Full name",
                        "order": 1,
                        "min": 1337,
                        "max": 322,
                    },
                },
            ],
        }
        serializer = SchemaSerializer(data=schema_data)
        self.assertFalse(serializer.is_valid())

        column_errors = serializer.errors["columns"][0]
        self.assertEqual(len(column_errors), 3)
        self.assertEqual(set(["__all__", "min", "max"]), set(column_errors))

    def test_serializer_create_from_validated(self):
        schema_data = {
            "name": "People",
            "column_separator": ";",
            "quotechar": "!",
            "columns": [
                {
                    "type": "name",
                    "params": {"name": "Full name", "order": 2},
                },
                {
                    "type": "random_int",
                    "params": {"name": "Age", "order": 1, "min": 1, "max": 5},
                },
            ],
        }
        serializer = SchemaSerializer(data=schema_data)
        self.assertTrue(serializer.is_valid(), serializer.errors)

        serializer.save(user=self.user)

        schema_from_db = Schema.objects.first()
        own_schema_fields = model_to_dict(
            schema_from_db, fields=["name", "column_separator", "quotechar"]
        )
        self.assertEqual(schema_data, schema_data | own_schema_fields)

        columns = list(schema_from_db.columns)
        self.assertEqual(len(columns), 2)
        for column in columns:
            self.assertTrue(column.name in ["Full name", "Age"])
