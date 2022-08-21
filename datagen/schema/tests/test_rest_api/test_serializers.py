from types import SimpleNamespace

from django.test import TestCase
from django.contrib.auth import get_user_model

from ...rest_api.serializers import SchemaSerializer


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
                }
            ],
        }
        # request = SimpleNamespace(user=self.user)
        serializer = SchemaSerializer(data=schema_data)
        print('schema: ', serializer)
        self.assertTrue(serializer.is_valid())
        validated = serializer.validated_data
        print('validated:', validated)

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
        # request = SimpleNamespace(user=self.user)
        serializer = SchemaSerializer(data=schema_data)
        print('schema: ', serializer)
        self.assertFalse(serializer.is_valid())
        print(serializer.errors)
        validated = serializer.validated_data
        print('validated:', validated)

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
        # request = SimpleNamespace(user=self.user)
        serializer = SchemaSerializer(data=schema_data)
        print('schema: ', serializer)
        self.assertFalse(serializer.is_valid())
        print(serializer.errors)
        validated = serializer.validated_data
        print('validated:', validated)

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
        # request = SimpleNamespace(user=self.user)
        serializer = SchemaSerializer(data=schema_data)
        print('schema: ', serializer)
        self.assertFalse(serializer.is_valid())
        print(serializer.errors)
        validated = serializer.validated_data
        print('validated:', validated)
        
