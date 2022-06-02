from unittest import TestCase
from datetime import datetime

from django import forms
from factory import Faker, ListFactory

from ...tests import AssertBetweenMixin

from ...forms.field_forms import (
    BaseFieldForm,
    RandomIntFieldForm,
    SentencesFieldForm,
    FIELD_FORMS,
)
from ...forms import field_forms
from ...services.generator import Field


class TestFieldFormsBase(TestCase):
    def test_children_get_correct_label_and_f_type(self):
        class LabeledFieldForm(BaseFieldForm):
            type = "random_int"
            label = "Random integer"

        field_form = LabeledFieldForm()
        self.assertEqual(field_form.label, "Random integer")
        self.assertEqual(field_form.fields["f_type"].initial, "random_int")

        class UnlabeledFieldForm(BaseFieldForm):
            type = "safe_email"

        field_form = UnlabeledFieldForm()

        self.assertEqual(field_form.label, "Safe email")

    def test_unset_base_fields_raises(self):
        class UnsetType(BaseFieldForm):
            pass

        with self.assertRaises(ValueError):
            UnsetType()

    def test_to_schema_field_method(self):
        field = Field(
            name="Age",
            f_type="random_int",
            f_params={"min": 18, "max": 65},
            order=3,
        )

        class RandomIntFieldForm(BaseFieldForm):
            type = "random_int"
            label = "Random integer"

            min = forms.IntegerField(
                label="Min",
                min_value=-9999999,
                max_value=9999999,
                required=True,
            )
            max = forms.IntegerField(
                label="Max",
                min_value=-9999999,
                max_value=9999999,
                required=True,
            )

        field_form = RandomIntFieldForm(field.to_dict())
        self.assertTrue(field_form.is_valid())
        self.assertDictEqual(
            field.to_dict(), field_form.to_schema_field().to_dict()
        )

    def test_form_field_has_correct_f_params(self):
        class RandomIntFieldForm(BaseFieldForm):
            type = "random_int"
            label = "Random integer"

            min = forms.IntegerField(
                label="Min",
                min_value=-9999999,
                max_value=9999999,
                required=True,
            )
            max = forms.IntegerField(
                label="Max",
                min_value=-9999999,
                max_value=9999999,
                required=True,
            )

        RandomIntFieldForm()  # to invoke cls.__new__
        self.assertTupleEqual(("min", "max"), RandomIntFieldForm.f_params)


class TestFieldFormsTraits(AssertBetweenMixin, TestCase):
    def get_Factory(self, f_type, f_params) -> ListFactory:
        return type("_Factory", (ListFactory,), {"field": Faker(f_type, **f_params)})  # type: ignore

    def get_sample_gen_data(self, cls, params=None):
        self.__dict__.setdefault("tested_classes", set()).add(cls)
        params = params or {}
        params["name"] = "Field name"
        params["order"] = 1
        params["f_type"] = cls.type
        inst = cls(data=params)
        self.assertTrue(inst.is_valid(), msg=inst.errors.as_data())
        return self.get_Factory(inst.type, inst._get_params())()[0]

    def test_min_max_validation_mixin_included(self):
        field_form = RandomIntFieldForm(
            data={
                "name": "Age",
                "f_type": "random_int",
                "order": 3,
                "min": 55,
                "max": 15,
            }
        )

        self.assertFalse(field_form.is_valid())
        self.assertListEqual(
            field_form.errors["min"], ["Min value must be less than max value"]
        )
        self.assertListEqual(
            field_form.errors["max"],
            ["Max value must be greater than min value"],
        )

        field_form = SentencesFieldForm(
            data={
                "name": "Lorem",
                "f_type": "sentences_variable_str",
                "order": 3,
                "nb_min": 55,
                "nb_max": 15,
            }
        )

        self.assertFalse(field_form.is_valid())
        self.assertListEqual(
            field_form.errors["nb_min"],
            ["Min value must be less than max value"],
        )
        self.assertListEqual(
            field_form.errors["nb_max"],
            ["Max value must be greater than min value"],
        )

    def test_field_forms_instantiates_to_faker_field(self):
        """Test that instantiating throws no errors and returns something sane. Also check that all the classes has been tested."""
        data = self.get_sample_gen_data(field_forms.FullNameFieldForm)
        self.assertIsInstance(data, str)
        self.assertGreater(len(data), 5)

        data = self.get_sample_gen_data(
            field_forms.RandomIntFieldForm, {"min": 18, "max": 65}
        )
        self.assertIsInstance(data, int)

        data = self.get_sample_gen_data(field_forms.JobFieldForm)
        self.assertIsInstance(data, str)
        self.assertGreater(len(data), 3)

        data = self.get_sample_gen_data(field_forms.EmailFieldForm)
        self.assertIsInstance(data, str)
        self.assertGreater(len(data), 5)
        self.assertIn("@", data)

        data = self.get_sample_gen_data(field_forms.PhoneNumberFieldForm)
        self.assertIsInstance(data, str)
        self.assertGreater(len(data), 1)
        self.assertTrue(any(data.isdigit() for data in data))

        data = self.get_sample_gen_data(field_forms.DomainFieldForm)
        self.assertIsInstance(data, str)
        self.assertGreater(len(data), 1)
        second, top = data.split(".")
        self.assertBetween(len(top), 2, 7)

        data = self.get_sample_gen_data(field_forms.CompanyFieldForm)
        self.assertIsInstance(data, str)
        self.assertGreater(len(data), 1)

        data = self.get_sample_gen_data(field_forms.AddressFieldForm)
        self.assertIsInstance(data, str)
        self.assertGreater(len(data), 1)

        data = self.get_sample_gen_data(field_forms.DateFieldForm)
        self.assertIsInstance(data, str)
        datetime.fromisoformat(data)

        data = self.get_sample_gen_data(
            field_forms.SentencesFieldForm, {"nb_min": 1, "nb_max": 2}
        )
        self.assertIsInstance(data, str)
        self.assertBetween(len(data), 5, 100)

        self.assertSetEqual(
            self.tested_classes,
            set(FIELD_FORMS.values()),
            msg="Not all field forms were tested.",
        )
