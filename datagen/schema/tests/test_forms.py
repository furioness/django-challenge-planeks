from django.contrib.auth import get_user_model
from django.contrib.auth.models import Permission
from django.forms.models import model_to_dict
from django.test import TestCase

from ..forms import GenerateForm, SchemaForm
from ..models import Schema, NameColumn, RandomIntColumn


class TestSchemaFormCase(TestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()  # required by django
        cls.user = get_user_model().objects.create_user(  # type: ignore
            username="testuser", password="12345"
        )

    @staticmethod
    def copy_form_prepared(dict_, prefix, idx: int | None = 0) -> dict:
        copy = {}
        if idx is not None:
            for key in dict_.keys():
                copy[f"{prefix}-{idx}-{key}"] = dict_[key]
        else:
            for key in dict_.keys():
                copy[f"{prefix}-{key}"] = dict_[key]

        return copy

    @staticmethod
    def get_management_form(prefix, total=1, initial=0) -> dict:
        return {
            f"{prefix}-TOTAL_FORMS": total,
            f"{prefix}-INITIAL_FORMS": initial,
        }

    def test_simple_data_instantiation_from_instance(self):
        schema = Schema.objects.create(
            name="Test schema",
            column_separator=",",
            quotechar='"',
            user=self.user,
        )
        NameColumn.objects.create(name="Name", order=1, schema=schema)
        RandomIntColumn.objects.create(
            name="Age", order=2, max=55, min=5, schema=schema
        )

        form = SchemaForm(instance=schema, user=self.user)
        self.assertIn('name="name" value="Test schema"', form.as_p())
        self.assertIn('name="column_separator" value=","', form.as_p())
        self.assertIn('name="quotechar" value="&quot;"', form.as_p())

        name_form = form.column_formsets[0]
        self.assertIn(
            'name="NameColumn-0-name" value="Name"', name_form.as_p()
        )
        self.assertIn('name="NameColumn-0-order" value="1"', name_form.as_p())

        random_int_form = form.column_formsets[1]
        self.assertIn(
            'name="RandomIntColumn-0-name" value="Age"', random_int_form.as_p()
        )
        self.assertIn(
            'name="RandomIntColumn-0-order" value="2"', random_int_form.as_p()
        )
        self.assertIn(
            'name="RandomIntColumn-0-max" value="55"', random_int_form.as_p()
        )
        self.assertIn(
            'name="RandomIntColumn-0-min" value="5"', random_int_form.as_p()
        )
        self.assertNotIn("schema", random_int_form.as_p())

    def test_simple_data_instantiation_from_data(self):
        schema_data = {
            "name": "Test form",
            "column_separator": ",",
            "quotechar": '"',
        }
        name_col_data = {"name": "Name", "order": 1}
        random_int_data = {
            "name": "Age",
            "order": 2,
            "min": 5,
            "max": 55,
        }
        form_data = {
            **schema_data,
            **self.copy_form_prepared(name_col_data, "NameColumn"),
            **self.get_management_form("NameColumn"),
            **self.copy_form_prepared(random_int_data, "RandomIntColumn"),
            **self.get_management_form("RandomIntColumn"),
        }
        form = SchemaForm(form_data, user=self.user)
        self.assertTrue(form.is_valid())
        form.save()

        schema = Schema.objects.get(name="Test form")
        self.assertDictEqual(
            model_to_dict(
                schema, fields=("name", "column_separator", "quotechar")
            ),
            schema_data,
        )

        self.assertDictEqual(
            model_to_dict(
                NameColumn.objects.get(name="Name"), fields=("name", "order")
            ),
            name_col_data,
        )

        self.assertDictEqual(
            model_to_dict(
                RandomIntColumn.objects.get(name="Age"),
                fields=("name", "order", "min", "max"),
            ),
            random_int_data,
        )

    def test_column_deletion(self):
        schema = Schema.objects.create(
            name="Test schema",
            column_separator=",",
            quotechar='"',
            user=self.user,
        )
        name = NameColumn.objects.create(name="Name", order=1, schema=schema)
        rand_int = RandomIntColumn.objects.create(
            name="Age", order=2, max=55, min=5, schema=schema
        )

        form_data = {
            **model_to_dict(schema),
            **self.copy_form_prepared(model_to_dict(name), "NameColumn"),
            **self.copy_form_prepared(
                model_to_dict(rand_int), "RandomIntColumn"
            ),
            **self.copy_form_prepared({"DELETE": True}, "RandomIntColumn"),
            **self.get_management_form("NameColumn", initial=1),
            **self.get_management_form("RandomIntColumn", initial=1),
        }

        form = SchemaForm(form_data, instance=schema, user=self.user)
        self.assertTrue(form.is_valid())

        form.save()
        with self.assertRaises(rand_int.DoesNotExist):
            rand_int.refresh_from_db()

    def test_delete_all_columns_is_disallowed(self):
        schema = Schema.objects.create(
            name="Test schema",
            column_separator=",",
            quotechar='"',
            user=self.user,
        )
        name = NameColumn.objects.create(name="Name", order=1, schema=schema)
        rand_int = RandomIntColumn.objects.create(
            name="Age", order=2, max=55, min=5, schema=schema
        )

        form_data = {
            **model_to_dict(schema),
            **self.copy_form_prepared(model_to_dict(name), "NameColumn"),
            **self.copy_form_prepared({"DELETE": True}, "NameColumn"),
            **self.copy_form_prepared(
                model_to_dict(rand_int), "RandomIntColumn"
            ),
            **self.copy_form_prepared({"DELETE": True}, "RandomIntColumn"),
            **self.get_management_form("NameColumn", initial=1),
            **self.get_management_form("RandomIntColumn", initial=1),
        }

        form = SchemaForm(form_data, instance=schema, user=self.user)
        self.assertFalse(form.is_valid())
        self.assertListEqual(
            form.errors["__all__"], ["Add at least one column."]
        )
        # should not rise
        name.refresh_from_db()
        rand_int.refresh_from_db()

    def test_validating_schema_own_fields(self):
        schema_data = {
            "name": "",
            "column_separator": "more than one character",
            "quotechar": "more than one character",
        }
        name_col_data = {"name": "Name", "order": 1}
        form_data = {
            **schema_data,
            **self.copy_form_prepared(name_col_data, "NameColumn"),
            **self.get_management_form("NameColumn"),
        }
        form = SchemaForm(form_data, user=self.user)
        self.assertFalse(form.is_valid())
        self.assertEqual(len(form.errors), 4)
        self.assertListEqual(form.errors["name"], ["This field is required."])
        self.assertListEqual(
            form.errors["quotechar"],
            ["Ensure this value has at most 1 character (it has 23)."],
        )
        self.assertListEqual(
            form.errors["quotechar"], form.errors["column_separator"]
        )

    def test_validating_no_columns(self):
        schema_data = {
            "name": "Test form",
            "column_separator": ",",
            "quotechar": '"',
        }
        form_data = {**schema_data}
        form = SchemaForm(form_data, user=self.user)
        self.assertFalse(form.is_valid())
        self.assertListEqual(
            form.errors["__all__"], ["Add at least one column."]
        )

    def test_validate_columns_errors_and_schema_errors(self):
        """As example would be min > max. And some schema errors."""

        schema_data = {
            "name": "Test form",
            "column_separator": "too long",
            "quotechar": '"',
        }
        name_col_data = {"name": "Some name", "order": 1}  # order 1 is default
        random_int_data = {
            "name": "Some age",
            "order": 1,
            "min": 5,
            "max": 1,
        }
        form_data = {
            **schema_data,
            **self.copy_form_prepared(name_col_data, "NameColumn"),
            **self.copy_form_prepared(random_int_data, "RandomIntColumn"),
            **self.get_management_form("NameColumn", 1),
            **self.get_management_form("RandomIntColumn", 1),
        }

        form = SchemaForm(form_data, user=self.user, prefix="Schema")
        self.assertFalse(form.is_valid(), form.data)
        self.assertListEqual(
            form.errors["__all__"], ["One or more columns have errors."]
        )
        self.assertListEqual(
            form.column_formsets[1][0].errors["__all__"],
            ["Min must be less than max."],
        )
        self.assertListEqual(
            form.column_formsets[1][0].errors["min"],
            ["Min must be less than max."],
        )
        self.assertListEqual(
            form.column_formsets[1][0].errors["max"],
            ["Max must be greater than min."],
        )

    def test_validate_semi_empty_columns_with_nonempty_defaults(self):
        """Default formset implementation allows empty forms (even if extra=0),
        so if apply form with default fields set but other fields being empty,
        it will look like no data was changed, so validation and saving will be
        skipped. Yet, form counter will be incremented. Nasty stuff!
        """
        schema_data = {
            "name": "Test form",
            "column_separator": ",",
            "quotechar": '"',
        }
        name_col_data = {"name": "", "order": 1}  # order 1 is default
        name_col_data_2 = {"name": "normal col", "order": 2}
        random_int_data = {
            "name": "",
            "order": 13,
            "min": 1,
            "max": 100,
        }
        form_data = {
            **self.copy_form_prepared(schema_data, "Schema", idx=None),
            **self.copy_form_prepared(name_col_data, "NameColumn"),
            **self.copy_form_prepared(name_col_data_2, "NameColumn", 1),
            **self.copy_form_prepared(random_int_data, "RandomIntColumn"),
            **self.get_management_form("NameColumn", 1),
            **self.get_management_form("RandomIntColumn", 1),
        }

        form = SchemaForm(form_data, user=self.user, prefix="Schema")
        self.assertFalse(form.is_valid(), form.data)
        self.assertListEqual(
            form.errors["__all__"], ["One or more columns have errors."]
        )
        self.assertListEqual(
            form.column_formsets[0][0].errors["name"],
            ["This field is required."],
        )
        self.assertListEqual(
            form.column_formsets[1][0].errors["name"],
            ["This field is required."],
        )

    def test_validate_duplicate_field_names(self):
        """Default formset implementation allows empty forms (even if extra=0),
        so if apply form with default fields set but other fields being empty,
        it will look like no data was changed, so validation and saving will be
        skipped. Yet, form counter will be incremented. Nasty stuff!
        """
        schema_data = {
            "name": "Test form",
            "column_separator": "more than one char",
            "quotechar": '"',
        }
        name_col_data = {"name": "Name1", "order": 1}  # order 1 is default
        random_int_data = {
            "name": "Name1",
            "order": 2,
            "min": 1,
            "max": 100,
        }
        form_data = {
            **self.copy_form_prepared(schema_data, "Schema", idx=None),
            **self.copy_form_prepared(name_col_data, "NameColumn"),
            **self.copy_form_prepared(random_int_data, "RandomIntColumn"),
            **self.get_management_form("NameColumn", 1),
            **self.get_management_form("RandomIntColumn", 1),
        }

        form = SchemaForm(form_data, user=self.user, prefix="Schema")
        self.assertFalse(form.is_valid(), form.data)
        self.assertListEqual(
            form.errors["__all__"], ["One or more columns have errors."]
        )
        self.assertIn("column_separator", form.errors)

        self.assertListEqual(
            form.column_formsets[0][0].errors["name"],
            ["This name is already used by another column."],
        )
        self.assertListEqual(
            form.column_formsets[0][0].errors["name"],
            form.column_formsets[1][0].errors["name"],
        )


class TestGenerateForm(TestCase):
    @classmethod
    def setUpTestData(cls):
        cls.user = get_user_model().objects.create_user(
            username="testuser", password="12345"
        )
        # TODO: solve the mystery: if creating cls.request here (and not overwrite in setUp), user.has_perm will fail.
        # cls.request = type(
        #     "", (), {"user": cls.user}
        # )()  # dot-accessible attribute. Do not name as `request` or magic bugs appear

    def setUp(self):
        self.request = type(
            "", (), {"user": self.user}
        )()  # dot-accessible attribute.

    def test_limited_rows_for_plebs(self):
        self.assertFalse(self.user.has_perm("schema.unlimited_generation"))

        form = GenerateForm({"num_rows": int(1e100)}, request=self.request)
        self.assertFalse(form.is_valid())

        form = GenerateForm({"num_rows": 100}, request=self.request)
        self.assertTrue(form.is_valid(), form.errors.as_json())

    def test_unlimited_rows_for_privileged_user(self):
        permission = Permission.objects.get(codename="unlimited_generation")
        self.user.user_permissions.add(permission)
        self.assertTrue(self.user.has_perm("schema.unlimited_generation"))

        form = GenerateForm({"num_rows": int(1e100)}, request=self.request)
        self.assertTrue(form.is_valid(), form.errors)
