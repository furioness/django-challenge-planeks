import csv
import json
import os
from statistics import mean
from typing import Generator
from unittest import TestCase

from factory import Faker, ListFactory

from ..services.data_saving import generate_to_csv
from ..services.generator import Field, Schema
from ..tests import AssertBetweenMixin


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

    def assertSchemaFieldsEqual(self, schema_given, schema_expected):
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
        self.assertSchemaFieldsEqual(
            Schema.from_dict_list(list_of_field_dicts), Schema(self.fields)
        )

    def test_to_JSON(self):
        schema = Schema(self.fields)
        schema_json = schema.to_JSON()
        self.assertSchemaFieldsEqual(
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


class TestCustomSentencesProvider(TestCase, AssertBetweenMixin):
    """Test LoremProvider_en_US with sentences_variable_str()
    Check https://github.com/joke2k/faker/tree/master/tests for inspiration"""

    def test_formatter_is_registered(self):
        class TestFactory(ListFactory):
            lorem = Faker("sentences_variable_str")

        TestFactory()

    def test_basic_string_generation(self):
        class TestFactory(ListFactory):
            lorem = Faker("sentences_variable_str")

        row = TestFactory()
        self.assertIsInstance(row, list)
        self.assertTrue(len(row), 1)
        self.assertIsInstance(row[0], str)
        self.assertGreater(len(row[0]), 0)

    def test_string_genration_parameterized(self):
        # it's hard to distinguish between a sentence, so looking for statistical significance in string length
        class SingleSentence(ListFactory):
            lorem = Faker("sentences_variable_str", nb_min=1, nb_max=1)

        class FourSentenced(ListFactory):
            lorem = Faker("sentences_variable_str", nb_min=4, nb_max=4)

        class OneToFourSentences(ListFactory):
            lorem = Faker("sentences_variable_str", nb_min=1, nb_max=4)

        singles = [SingleSentence()[0] for _ in range(50)]
        mean_1 = mean(len(sentence) for sentence in singles)
        total_1 = sum(len(sentence) for sentence in singles)

        fourths = [FourSentenced()[0] for _ in range(50)]
        mean_4 = mean(len(sentence) for sentence in fourths)
        total_4 = sum(len(sentence) for sentence in fourths)

        one_to_fourths = [OneToFourSentences()[0] for _ in range(50)]
        mean_1_to_4 = mean(len(sentence) for sentence in one_to_fourths)
        total_1_to_4 = sum(len(sentence) for sentence in one_to_fourths)

        self.assertBetween(mean_1_to_4, mean_1, mean_4)
        self.assertBetween(total_1_to_4, total_1, total_4)
        # then maybe test some statistical stuff, but there isn't much to get broken, so enough just to test it manually once. So I did.


class TestCSVSaving(TestCase):
    def test_data_saving(self):
        header = ["name", "age"]
        data = [["Vasya", "25"], ["Zucc", "38"]]
        delimiter = "!"
        quotechar = "~"

        file = generate_to_csv(
            generator=iter(data),
            header=header,
            delimiter=delimiter,
            quotechar=quotechar,
        )
        with open(file, "r") as f:
            csv_reader = csv.reader(
                f, delimiter=delimiter, quotechar=quotechar
            )
            self.assertListEqual(next(csv_reader), header)
            self.assertListEqual(list(csv_reader), data)

        os.remove(file)
