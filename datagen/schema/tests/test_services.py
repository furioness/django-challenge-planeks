# TODO: investigate possible usage of factory.random.set_random_state() to work with determined generated data

import csv
import os
from statistics import mean
from typing import Generator as GeneratorType

from django.test import SimpleTestCase
from factory import Faker, ListFactory

from ..services.data_saving import generate_to_csv
from ..services.generator import ColumnDTO, Generator
from ..tests import AssertBetweenMixin


class TestSchema(SimpleTestCase, AssertBetweenMixin):
    """Test Schema using unittest TestCase as transactions not required"""

    def setUp(self) -> None:
        self.rand_int_params = {"min": 18, "max": 65}
        self.columns = [
            ColumnDTO("Full name", "name", 0, {}),
            ColumnDTO("Company", "company", 2, {}),
            ColumnDTO("Age", "random_int", 1, self.rand_int_params),
        ]
        self.sorted_header = ["Full name", "Age", "Company"]

    def assertSchemaFieldsEqual(self, schema_given, schema_expected):
        fields_given = [field.to_dict() for field in schema_given.fields]
        fields_excepted = [field.to_dict() for field in schema_expected.fields]
        self.assertListEqual(fields_given, fields_excepted)

    def test_correct_init(self):
        """ "Test that schema correctly sorts fields and parses the header"""
        generator = Generator(self.columns)

        self.assertEqual(
            [field.name for field in generator.fields], self.sorted_header
        )

        self.assertEqual(generator.header, self.sorted_header)

    def test_get_generator(self):
        """Return a Factory class with correct fields and their params"""
        generator = Generator(self.columns)
        factory = generator._get_Factory()
        field_params_dict = {
            field.provider: field._defaults
            for field in factory._meta.declarations.values()
        }
        for param in field_params_dict.values():
            del param["locale"]

        self.assertDictEqual(
            field_params_dict,
            {field.type: field.params for field in self.columns},
        )

    def test_data_generator(self):
        """Test that data_generator returns a generator with correct number of records and fields, and fields of correct type"""
        generator = Generator(self.columns)
        generator_yielder = generator.generate(num_records=10)
        self.assertIsInstance(generator_yielder, GeneratorType)
        records = list(generator_yielder)

        self.assertIsInstance(records[0], list)
        self.assertEqual(len(records), 10)

        self.assertEqual(len(records[0]), len(self.columns))

        self.assertIsInstance(records[0][0], str)
        self.assertIsInstance(records[0][1], int)
        self.assertIsInstance(records[0][2], str)

    def test_data_generator_uses_field_params(self):
        """Test param application on example of random_int field"""
        int_min = 5
        int_max = 105

        field = ColumnDTO(
            "Number", "random_int", 0, {"min": int_min, "max": int_max}
        )
        generator = Generator([field])

        ints = [record[0] for record in generator.generate(num_records=100)]

        # check that all ints are in range
        for int in ints:
            self.assertBetween(int, int_min, int_max)

        # and that they are not all the same
        # delta 20 is enough on 100 items here
        self.assertAlmostEqual(mean(ints), mean([int_min, int_max]), delta=20)


class TestCustomSentencesProvider(SimpleTestCase, AssertBetweenMixin):
    """Test LoremProvider_en_US with sentences_variable_str()
    Check https://github.com/joke2k/faker/tree/master/tests for inspiration"""

    def test_formatter_is_registered(self):
        class TestFactory(ListFactory):
            lorem = Faker("sentences_variable_str")

        TestFactory()

    def test_basic_string_generation(self):
        class TestFactory(ListFactory):
            lorem = Faker("sentences_variable_str")

        row: list = TestFactory() # type: ignore
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

        singles = [SingleSentence()[0] for _ in range(50)]  # type: ignore
        mean_1 = mean(len(sentence) for sentence in singles)
        total_1 = sum(len(sentence) for sentence in singles)

        fourths = [FourSentenced()[0] for _ in range(50)]  # type: ignore
        mean_4 = mean(len(sentence) for sentence in fourths)
        total_4 = sum(len(sentence) for sentence in fourths)

        one_to_fourths = [OneToFourSentences()[0] for _ in range(50)]  # type: ignore
        mean_1_to_4 = mean(len(sentence) for sentence in one_to_fourths)
        total_1_to_4 = sum(len(sentence) for sentence in one_to_fourths)

        self.assertBetween(mean_1_to_4, mean_1, mean_4)
        self.assertBetween(total_1_to_4, total_1, total_4)
        # then maybe test some statistical stuff, but there isn't much to get broken, so enough just to test it manually once. So I did.


class TestCSVSaving(SimpleTestCase):
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
