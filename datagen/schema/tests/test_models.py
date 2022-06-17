from datetime import timedelta
from unittest import mock

from django.contrib.auth import get_user_model
from django.core.exceptions import ValidationError
from django.test import TestCase
from django.utils import timezone
from factory import Faker, ListFactory

from ..models import (BaseColumn, CheckAttrsMeta, Dataset, NameColumn,
                      RandomIntColumn, Schema, SentencesColumn)
from ..services.generator import Generator


class TestSchema(TestCase):
    @classmethod
    def setUpTestData(cls):
        cls.user = get_user_model().objects.create_user(  # type: ignore
            username="testuser", password="12345"
        )

    def test_model_instantiation(self):
        schema = Schema.objects.create(name="Test schema", user=self.user)
        NameColumn.objects.create(name="Name col", schema=schema)
        self.assertEqual(Schema.objects.get(user=self.user), schema)
        self.assertEqual(schema.name, "Test schema")
        self.assertEqual(schema.user, self.user)
        self.assertAlmostEqual(
            schema.modified, timezone.now(), delta=timedelta(seconds=5)
        )

    def test_returns_data_generator(self):
        schema: Schema = Schema.objects.create(
            name="Test schema", user=self.user
        )
        NameColumn.objects.create(name="Name col", schema=schema)
        gen_schema = schema.get_generator
        self.assertIsInstance(gen_schema, Generator)
        self.assertTrue(len(gen_schema.fields), 1)
        self.assertEqual(gen_schema.fields[0].name, "Name col")

    def test_to_str(self):
        """Test that schema string representation isn't crashing"""
        str(Schema.objects.create(name="Test", user=self.user))  # NOSONAR

    def test_returns_columns(self):
        schema = Schema.objects.create(name="Test schema", user=self.user)
        columns = [
            NameColumn.objects.create(name="Name col", schema=schema),
            NameColumn.objects.create(name="Name col 2", schema=schema),
            RandomIntColumn.objects.create(
                name="Random int col", schema=schema
            ),
        ]
        # This assertion will fail if unequal order,
        # but for simplicity let it be this way
        self.assertListEqual(list(schema.columns), columns)

    def test_calls_genration_task(self):
        from .. import tasks

        schema: Schema = Schema.objects.create(
            name="Test schema", user=self.user
        )
        NameColumn.objects.create(name="Name col", schema=schema)

        self.assertEqual(schema.datasets.count(), 0)  # type: ignore
        with mock.patch.object(tasks, "generate_data", mock.Mock()) as task:
            schema.run_generate_task(num_rows=10)
            gen_data = schema.datasets.first()  # type: ignore
            task.delay.assert_called_once_with(gen_data.id)
            self.assertEqual(gen_data.num_rows, 10)

    def test_cascade_deletion_on_user(self):
        schema_id: Schema = Schema.objects.create(
            name="Test schema", user=self.user
        ).id
        self.user.delete()
        with self.assertRaises(Schema.DoesNotExist):
            Schema.objects.get(pk=schema_id)


class TestGeneratedData(TestCase):
    @classmethod
    def setUpTestData(cls):
        cls.user = get_user_model().objects.create_user(  # type: ignore
            username="testuser", password="12345"
        )
        cls.schema = Schema.objects.create(
            name="Test schema",
            user=cls.user,
        )
        NameColumn.objects.create(name="Name col", schema=cls.schema),

    def test_model_instantiation(self):
        gen_data = Dataset.objects.create(schema=self.schema, num_rows=10)
        self.assertEqual(gen_data.schema, self.schema)
        self.assertEqual(gen_data.num_rows, 10)
        self.assertFalse(gen_data.file)
        self.assertAlmostEqual(
            gen_data.created,
            timezone.now(),
            delta=timedelta(seconds=5),
        )

    def test_cascade_deletion(self):
        self.assertEqual(0, self.schema.datasets.count())  # type: ignore
        gen_data_id = Dataset.objects.create(
            schema=self.schema, num_rows=10
        ).id
        self.assertEqual(1, self.schema.datasets.count())  # type: ignore
        self.schema.delete()
        with self.assertRaises(Dataset.DoesNotExist):
            Dataset.objects.get(pk=gen_data_id)


class TestAttrsMetaClass(TestCase):
    def test_ensures_type_and_label(self):
        with self.assertRaisesMessage(
            AttributeError, "Test has no type specified."
        ):
            CheckAttrsMeta("Test", (), {})

    def test_generate_label_from_type(self):
        meta = CheckAttrsMeta("Test", (), {"type": "test_type"})
        self.assertEqual(meta.label, "Test Type")


class TestSimpleColumns(TestCase):
    @classmethod
    def setUpTestData(cls):
        cls.user = get_user_model().objects.create_user(  # type: ignore
            username="testuser", password="12345"
        )
        cls.schema = Schema.objects.create(name="Test schema", user=cls.user)

    @staticmethod
    def simple_models():
        base_field_names = ["id"] + [
            field.name for field in BaseColumn._meta.fields
        ]
        return [
            model
            for model in BaseColumn.__subclasses__()
            if all(field.name in base_field_names for field in model._meta.fields)
        ]

    @staticmethod
    def get_Factory(type_, params) -> ListFactory:
        return type("_Factory", (ListFactory,), {"field": Faker(type_, **params)})  # type: ignore
    
    def test_simple_columns_instantiation(self):
        for column in self.simple_models():
            col = column.objects.create(schema=self.schema, name='Test col')
            self.assertEqual(col, column.objects.get(pk=col.id, name='Test col'))

    def test_simple_columns_have_existend_faker_type(self):
        for column in self.simple_models():
            self.assertIsNotNone(self.get_Factory(column.type, {})()[0])
            
    
class TestRandomIntColumn(TestCase):
    @classmethod
    def setUpTestData(cls):
        cls.user = get_user_model().objects.create_user(  # type: ignore
            username="testuser", password="12345"
        )
        cls.schema = Schema.objects.create(name="Test schema", user=cls.user)
        
    @staticmethod
    def get_Factory(type_, params) -> ListFactory:
        return type("_Factory", (ListFactory,), {"field": Faker(type_, **params)})  # type: ignore
    
    def test_column_instantiation(self):
        col = RandomIntColumn.objects.create(schema=self.schema, name='Test col')
        self.assertEqual(col, RandomIntColumn.objects.get(pk=col.id, name='Test col'))
        
        col = RandomIntColumn.objects.create(schema=self.schema, name='Test col 2', min=123, max=567)
        self.assertEqual(col, RandomIntColumn.objects.get(pk=col.id, name='Test col 2', min=123, max=567))
        
    def test_invalidates_incorrect_min_max(self):
        col = RandomIntColumn(schema=self.schema, name='Test col 2', min=765, max=432)
        self.assertRaises(ValidationError, col.full_clean)
        
        
class TestRandomIntColumn(TestCase):
    @classmethod
    def setUpTestData(cls):
        cls.user = get_user_model().objects.create_user(  # type: ignore
            username="testuser", password="12345"
        )
        cls.schema = Schema.objects.create(name="Test schema", user=cls.user)
        
    @staticmethod
    def get_Factory(type_, params) -> ListFactory:
        return type("_Factory", (ListFactory,), {"field": Faker(type_, **params)})  # type: ignore
    
    def test_column_instantiation(self):
        col = RandomIntColumn.objects.create(schema=self.schema, name='Test col')
        self.assertEqual(col, RandomIntColumn.objects.get(pk=col.id, name='Test col'))
        
        col = RandomIntColumn.objects.create(schema=self.schema, name='Test col 2', min=123, max=567)
        self.assertEqual(col, RandomIntColumn.objects.get(pk=col.id, name='Test col 2', min=123, max=567))
        
    def test_column_have_existend_faker_type(self):
        self.assertIsNotNone(self.get_Factory(RandomIntColumn.type, {})()[0])
        
    def test_invalidates_incorrect_min_max(self):
        col = RandomIntColumn(schema=self.schema, name='Test col 2', min=765, max=432)
        self.assertRaises(ValidationError, col.full_clean)
        
        
class TestSentencesField(TestCase):
    @classmethod
    def setUpTestData(cls):
        cls.user = get_user_model().objects.create_user(  # type: ignore
            username="testuser", password="12345"
        )
        cls.schema = Schema.objects.create(name="Test schema", user=cls.user)
        
    @staticmethod
    def get_Factory(type_, params) -> ListFactory:
        return type("_Factory", (ListFactory,), {"field": Faker(type_, **params)})  # type: ignore
    
    def test_column_instantiation(self):
        col = SentencesColumn.objects.create(schema=self.schema, name='Test col')
        self.assertEqual(col, SentencesColumn.objects.get(pk=col.id, name='Test col'))
        
        col = SentencesColumn.objects.create(schema=self.schema, name='Test col 2', nb_min=123, nb_max=567)
        self.assertEqual(col, SentencesColumn.objects.get(pk=col.id, name='Test col 2', nb_min=123, nb_max=567))
        
    def test_column_have_existend_faker_type(self):
        self.assertIsNotNone(self.get_Factory(SentencesColumn.type, {})()[0])
        
    def test_invalidates_incorrect_min_max(self):
        col = SentencesColumn(schema=self.schema, name='Test col 2', nb_min=765, nb_max=432)
        self.assertRaises(ValidationError, col.full_clean)
