"""There is some duplication of tests for Column and Schema serializers,
but it's kind of fine as I want to see correct error output."""

import unittest
from copy import deepcopy

from django.test import TestCase
from django.contrib.auth import get_user_model
from django.forms.models import model_to_dict

from ...rest_api.serializers import ColumnSerializer, SchemaSerializer
from ...models import NameColumn, RandomIntColumn, Schema


class TestColumnSerializer(TestCase):
    name_column = {"type": "name", "params": {"name": "Full name", "order": 2}}
    rand_int_column = {
        "type": "random_int",
        "params": {"name": "Age", "order": 1, "min": 1, "max": 5},
    }

    @classmethod
    def setUpTestData(cls):
        user = get_user_model().objects.create_user(
            username="testuser", password="12345"
        )
        cls.schema = Schema.objects.create(
            **{
                "name": "People",
                "column_separator": ";",
                "quotechar": "!",
            },
            user=user
        )
        cls.name_column = NameColumn.objects.create(
            name="Vasya", order=1, schema=cls.schema
        )

    def test_serialize_normal__to_internal_value(self):
        col_data = {
            "type": "random_int",
            "params": {
                "name": "Age",
                "order": 1,
                "min": 123,
                "max": 456,
            },
        }
        serializer = ColumnSerializer(data=col_data)
        self.assertTrue(serializer.is_valid(), serializer.errors)
        instance = serializer.to_internal_value(serializer.data)

        self.assertEqual(instance.type, col_data["type"])
        self.assertDictEqual(
            model_to_dict(instance),
            model_to_dict(instance) | col_data["params"],
        )

    def test_deserialize_normal(self):
        serializer = ColumnSerializer(instance=self.name_column)
        representation = serializer.data

        self.assertEqual(representation["type"], "name")
        self.assertEqual(
            list(representation["params"].items()),
            [("name", "Vasya"), ("order", 1)],
        )

    def test_validates_for_missing_top_level_keys(self):
        col_data_params_missed = {"type": "random_int"}
        col_data_type_missed = {
            "params": {
                "name": "Age",
                "order": 1,
                "min": 123,
                "max": 456,
            }
        }

        serializer = ColumnSerializer(data=col_data_params_missed)
        self.assertFalse(serializer.is_valid())
        self.assertTrue("params" in serializer.errors)

        serializer = ColumnSerializer(data=col_data_type_missed)
        self.assertFalse(serializer.is_valid())
        self.assertTrue("type" in serializer.errors)

    def test_validates_for_missing_params(self):
        col_data = {
            "type": "random_int",
            "params": {
                "name": "Age",
                # "order": 1, - missed
                "min": 123,
                "max": 456,
            },
        }

        serializer = ColumnSerializer(data=col_data)
        self.assertFalse(serializer.is_valid())
        self.assertTrue("params" in serializer.errors)
        self.assertTrue("order" in serializer.errors["params"])

    def test_validates_for_invalid_param_values(self):
        bad_rand_int_col_data = {
            "type": "random_int",
            "params": {
                "name": "Full name",
                "order": 1,
                "min": 1337,  # min > max
                "max": 322,
            },
        }
        serializer = ColumnSerializer(data=bad_rand_int_col_data)
        self.assertFalse(serializer.is_valid())

        self.assertTrue("params" in serializer.errors)
        self.assertTupleEqual(
            tuple(serializer.errors["params"].keys()),
            ("__all__", "min", "max"),
        )

    def test_validates_for_invalid_col_type(self):
        bad_rand_int_col_data = {
            "type": "invalid_type",
            "params": {"whatever": 123},
        }
        serializer = ColumnSerializer(data=bad_rand_int_col_data)
        self.assertFalse(serializer.is_valid())

        self.assertTrue("type" in serializer.errors)

    @unittest.skip(
        reason="Seems like it's the default behavior for DRF to allow superfluous fields."
    )
    def test_serialize_nonexistent_col_param(self):
        bad_rand_int_col_data = {
            "type": "random_int",
            "params": {
                "name": "Full name",
                "order": 1,
                "nonexistent_param": 1337,
            },
        }

        serializer = ColumnSerializer(data=bad_rand_int_col_data)
        self.assertFalse(serializer.is_valid())


class TestSchemaSerializer(TestCase):
    schema_data_normal = {
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

    @classmethod
    def setUpTestData(cls):
        cls.user = get_user_model().objects.create_user(
            username="testuser", password="12345"
        )

    def test_serialize_normal(self):
        serializer = SchemaSerializer(data=self.schema_data_normal)
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

    def test_serializer_create_from_validated(self):
        serializer = SchemaSerializer(data=self.schema_data_normal)
        self.assertTrue(serializer.is_valid(), serializer.errors)

        instance = serializer.save(user=self.user)

        schema_from_db = Schema.objects.first()
        self.assertEqual(instance, schema_from_db)
        own_schema_fields = model_to_dict(
            schema_from_db, fields=["name", "column_separator", "quotechar"]
        )
        self.assertEqual(
            self.schema_data_normal,
            self.schema_data_normal | own_schema_fields,
        )

        columns = list(schema_from_db.columns)
        self.assertEqual(len(columns), 2)
        for column in columns:
            self.assertTrue(column.name in ["Full name", "Age"])

    def test_serializer_update(self):
        serializer = SchemaSerializer(data=self.schema_data_normal)
        self.assertTrue(serializer.is_valid(), serializer.errors)
        instance = serializer.save(user=self.user)

        schema_data_updated = deepcopy(self.schema_data_normal)
        schema_data_updated["name"] = "Humans"
        schema_data_updated["columns"].pop()
        schema_data_updated["columns"].append(
            {"type": "job", "params": {"name": "Occupation", "order": 3}}
        )
        serializer_updated = SchemaSerializer(
            instance=instance, data=schema_data_updated
        )
        self.assertTrue(
            serializer_updated.is_valid(), serializer_updated.errors
        )

        instance_updated = serializer_updated.save()
        self.assertEqual(Schema.objects.count(), 1)

        schema_from_db = Schema.objects.first()
        self.assertEqual(instance_updated, schema_from_db)

        columns = list(schema_from_db.columns)
        self.assertEqual(len(columns), 2)
        job_col = [
            column
            for column in columns
            if column.type == "job" and column.name == "Occupation"
        ]
        self.assertTrue(job_col)
