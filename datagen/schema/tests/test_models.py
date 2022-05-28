from datetime import timedelta
from unittest import mock

from django.contrib.auth import get_user_model
from django.forms import Form
from django.test import TestCase
from django.utils import timezone

from ..models import GeneratedData, Schema
from ..services.generator import Schema as GenSchema


class TestSchema(TestCase):
    FIELDS = [
        {"name": "Full name", "order": 1, "f_type": "name", "f_params": {}},
    ]

    @classmethod
    def setUpTestData(cls):
        cls.user = get_user_model().objects.create_user(
            username="Vasya", email="vasya@invalid.doom", password="whocares"
        )

    def test_model_instantiation(self):
        schema = Schema.objects.create(
            name="Test schema", user=self.user, fields=self.FIELDS
        )
        self.assertEqual(Schema.objects.get(user=self.user), schema)
        self.assertEqual(schema.name, "Test schema")
        self.assertEqual(schema.user, self.user)
        self.assertEqual(schema.fields, self.FIELDS)
        self.assertAlmostEqual(
            schema.modified, timezone.now(), delta=timedelta(seconds=5)
        )

    def test_returns_data_generator(self):
        schema: Schema = Schema.objects.create(
            name="Test schema", user=self.user, fields=self.FIELDS
        )
        gen_schema = schema.gen_schema_instance
        self.assertIsInstance(gen_schema, GenSchema)
        self.assertListEqual(
            [field.to_dict() for field in gen_schema.fields], schema.fields
        )

    def test_to_str(self):
        """Test that schema string representation isn't crashing"""
        str(
            Schema.objects.create(
                name="Test schema", user=self.user, fields=self.FIELDS
            )
        )

    def test_returns_field_forms(self):
        """Test that schema returns field forms. Correctness of forms is tested in test_forms.py as field_forms defines schema.fields to list[Form] convertion"""
        schema = Schema.objects.create(
            name="Test schema", user=self.user, fields=self.FIELDS
        )
        forms = schema.get_field_forms()
        self.assertEqual(len(forms), len(self.FIELDS))
        self.assertIsInstance(forms[0], Form)

    def test_calls_genration_task(self):
        from .. import tasks

        schema: Schema = Schema.objects.create(
            name="Test schema", user=self.user, fields=self.FIELDS
        )
        self.assertEqual(schema.generated_data.count(), 0)
        with mock.patch.object(tasks, "generate_data", mock.Mock()) as task:
            schema.run_generate_task(num_rows=10)
            gen_data = schema.generated_data.first()
            task.delay.assert_called_once_with(gen_data.id)
            self.assertEqual(gen_data.num_rows, 10)

    def test_cascade_deletion(self):
        schema_id: Schema = Schema.objects.create(
            name="Test schema", user=self.user, fields=self.FIELDS
        ).id
        self.user.delete()
        with self.assertRaises(Schema.DoesNotExist):
            Schema.objects.get(pk=schema_id)

    class TestGeneratedData(TestCase):
        @classmethod
        def setUpTestData(cls):
            cls.user = get_user_model().objects.create_user(
                username="Vasya",
                email="vasya@invalid.doom",
                password="whocares",
            )
            cls.schema: Schema = Schema.objects.create(
                name="Test schema",
                user=cls.user,
                fields=[
                    {
                        "name": "Full name",
                        "order": 1,
                        "f_type": "name",
                        "f_params": {},
                    }
                ],
            )

        def test_model_instantiation(self):
            gen_data: GeneratedData = GeneratedData.objects.create(
                schema=self.schema, num_rows=10
            )
            self.assertEqual(gen_data.schema, self.schema)
            self.assertEqual(gen_data.num_rows, 10)
            self.assertFalse(gen_data.file)
            self.assertAlmostEqual(
                gen_data.modified, timezone.now(), delta=timedelta(seconds=5)
            )

        def test_cascade_deletion(self):
            self.assertEqual(0, self.schema.generated_data.count())
            gen_data_id = GeneratedData.objects.create(
                schema=self.schema, num_rows=10
            ).id
            self.assertEqual(1, self.schema.generated_data.count())
            self.schema.delete()
            with self.assertRaises(Schema.DoesNotExist):
                GeneratedData.objects.get(pk=gen_data_id)
