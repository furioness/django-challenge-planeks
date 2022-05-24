from statistics import mean
import json
from typing import Generator, List
from unittest import TestCase

from factory import Faker, ListFactory

from datagen.schema.services.generator import Schema, Field
from datagen.schema.services.providers import LoremProvider_en_US
from datagen.schema.tests import AssertBetweenMixin


class TestSchemaField(TestCase):
    """Test Schema Field using unittest TestCase as transactions not required"""

    KWARGS = {
        "name": "Some field",
        "f_type": "some_field_type",
        "f_params": {"param1": "param1Val"},
        "order": 2,
    }

    def test_to_dict(self):
        field = Field(**self.KWARGS)
        self.assertDictEqual(field.to_dict(), self.KWARGS)

    def test_to_str(self):
        """Test that it at least isn't crashes and return non-empty string"""
        self.assertTrue(str(Field(**self.KWARGS)))


class TestSchema(TestCase, AssertBetweenMixin):
    """Test Schema using unittest TestCase as transactions not required"""

    def setUp(self) -> None:
        self.rand_int_params = {"min": 18, "max": 65}
        self.fields = [
            Field("Full name", "name", {}, 0),
            Field("Company", "company", {}, 2),
            Field("Age", "random_int", self.rand_int_params, 1),
        ]
        self.sorted_header = ["Full name", "Age", "Company"]

    def assertFieldsEqual(self, schema_given, schema_expected):
        fields_given = [field.to_dict() for field in schema_given.fields]
        fields_excepted = [field.to_dict() for field in schema_expected.fields]
        self.assertListEqual(fields_given, fields_excepted)

    def test_correct_init(self):
        """ "Test that schema correctly sorts fields and parses the header"""
        schema = Schema(self.fields)

        self.assertEqual(
            [field.name for field in schema.fields], self.sorted_header
        )

        self.assertEqual(schema.header, self.sorted_header)

    def test_init_from_dict_list(self):
        list_of_field_dicts = [field.to_dict() for field in self.fields]
        # check equality by fields
        self.assertFieldsEqual(
            Schema.from_dict_list(list_of_field_dicts), Schema(self.fields)
        )

    def test_to_JSON(self):
        schema = Schema(self.fields)
        schema_json = schema.to_JSON()
        self.assertFieldsEqual(
            schema, Schema.from_dict_list(json.loads(schema_json))
        )

    def test_get_generator(self):
        """Return a Factory class with correct fields and their params"""
        schema = Schema(self.fields)
        factory = schema._get_Factory()
        field_params_dict = {
            field.provider: field._defaults
            for field in factory._meta.declarations.values()
        }
        for param in field_params_dict.values():
            del param["locale"]

        self.assertDictEqual(
            field_params_dict,
            {field.f_type: field.f_params for field in self.fields},
        )

    def test_data_generator(self):
        """Test that data_generator returns a generator with correct number of records and fields, and fields of correct type"""
        schema = Schema(self.fields)
        generator = schema.data_generator(num_records=10)
        self.assertIsInstance(generator, Generator)
        records = list(generator)

        self.assertIsInstance(records[0], list)
        self.assertEqual(len(records), 10)

        self.assertEqual(len(records[0]), len(self.fields))

        self.assertIsInstance(records[0][0], str)
        self.assertIsInstance(records[0][1], int)
        self.assertIsInstance(records[0][2], str)

    def test_data_generator_uses_field_params(self):
        """Test param application on example of random_int field"""
        int_min = 5
        int_max = 105

        field = Field(
            "Number", "random_int", {"min": int_min, "max": int_max}, 0
        )
        schema = Schema([field])

        generator = schema.data_generator(num_records=100)
        ints = [record[0] for record in generator]

        # check that all ints are in range
        for int in ints:
            self.assertBetween(int, int_min, int_max)

        # and that they are not all the same
        # delta 20 is enough on 100 items here
        self.assertAlmostEqual(mean(ints), mean([int_min, int_max]), delta=20)
