from typing import Any, Optional

from django import forms
from django.conf import settings
from django.contrib.auth.base_user import AbstractBaseUser
from django.db.models import Sum
from django.forms import ModelForm

from .models import BaseColumn, Dataset, Schema


class GenerateForm(forms.Form):
    num_rows = forms.IntegerField(label="Rows", min_value=1, initial=1234)

    def __init__(self, *args, **kwargs):  # type: ignore
        self.user = kwargs.pop("request").user
        super().__init__(*args, **kwargs)

    def clean_num_rows(self) -> int:
        num_rows: int = self.cleaned_data["num_rows"]
        if not self.user.has_perm("schema.unlimited_generation"):
            rows_used = (
                Dataset.objects.filter(schema__user=self.user).aggregate(
                    Sum("num_rows")
                )["num_rows__sum"]
                or 0
            )
            rows_left = settings.USER_GENERATION_ROW_LIMIT - rows_used

            if num_rows > rows_left:
                raise forms.ValidationError(
                    f"You have {rows_left} rows left. Please reduce the number of rows to {rows_left} or less."
                )

        return num_rows


class FieldSelectForm(forms.Form):
    name = forms.CharField(max_length=255)
    type = forms.ChoiceField(
        choices=(
            (Column.__name__, Column.label)
            for Column in BaseColumn.__subclasses__()
        ),
        label="Type",
    )
    order = forms.IntegerField(initial=1)
    column_form_templates = [
        (
            Column.__name__,
            forms.modelform_factory(Column, exclude=("id", "schema"))(
                prefix=Column.__name__ + "-!",
            ),
        )
        for Column in BaseColumn.__subclasses__()
    ]


class BaseColumnFormSet(forms.BaseModelFormSet):
    def __init__(self, *args, **kwargs):  # type: ignore[no-untyped-def]
        super().__init__(*args, **kwargs)
        # if user leave some fields empty,
        # but fields with default values will have their defaults,
        # form will look like it wasn't changed and validation (and saving)
        # will be skipped (see https://stackoverflow.com/questions/13745343/django-formsets-confusion-validation-required-empty-permitted)
        for form in self.forms:
            form.empty_permitted = False

    def get_deletion_widget(self) -> forms.Widget:
        return forms.HiddenInput(attrs={"class": "deletion"})


class ColumnWithOrderFieldLast(forms.ModelForm):
    def __new__(cls, *args, **kwargs):  # type: ignore[no-untyped-def]
        cls: type[ColumnWithOrderFieldLast] = super().__new__(cls)  # type: ignore[no-redef]
        fields = list(cls.base_fields.keys())
        fields.remove("order")
        cls.field_order = fields + ["order"]
        return cls


class SchemaForm(forms.ModelForm):
    class Meta:
        model = Schema
        fields = ("name", "column_separator", "quotechar")

    def __init__(self, data: Optional[dict] = None, *args, user: AbstractBaseUser, **kwargs):  # type: ignore
        self.user = user
        super().__init__(data, *args, **kwargs)
        self.column_formsets = [
            forms.modelformset_factory(
                col_model,
                form=ColumnWithOrderFieldLast,
                exclude=("id", "schema"),
                extra=0,
                can_delete=True,
                formset=BaseColumnFormSet,
            )(data=data, queryset=cols_qs, prefix=col_model.__name__)
            for col_model, cols_qs in self.instance.columns_grouped_by_type.items()
        ]

    def clean(self) -> Optional[dict[str, Any]]:  # type: ignore[override]
        schema_cleaned_data = super().clean()

        column_count = sum(
            formset.total_form_count() - len(formset.deleted_forms)
            for formset in self.column_formsets
        )
        if column_count == 0:
            self.add_error(None, "Add at least one column.")
            return None

        formsets_valid = [
            formset.is_valid() for formset in self.column_formsets
        ]

        # don't forget to propagate formsets errors to the main form by add_error() or the form will look like valid and will have save() called
        is_valid = all(formsets_valid)
        is_valid &= self._validate_duplicate_fields()
        if not is_valid:
            self.add_error(None, "One or more columns have errors.")

        # if the form isn't valid, it doesn't matter if we return here something or not as it isn't supposed to be used anyway
        return schema_cleaned_data

    def _validate_duplicate_fields(self) -> bool:
        """Check columns for duplicates in name field and add error message to the forms.
        Return True/False if valid/invalid."""
        name_forms: dict[str, list[ModelForm]] = {}
        for column_formset in self.column_formsets:
            for column_form in column_formset:
                if not (name := column_form.cleaned_data.get("name", None)):
                    continue
                name_forms.setdefault(name, []).append(column_form)
        valid = True
        for forms in name_forms.values():
            if len(forms) > 1:
                for form in forms:
                    form.add_error(
                        "name", "This name is already used by another column."
                    )
                    valid = False
        return valid

    def save(self, commit: bool = True) -> Schema:
        # if user is not set it will raise, so checking user_id
        self.instance: Schema
        if not self.instance.user_id:  # type: ignore
            self.instance.user = self.user
        schema = super().save(commit)

        for column_formset in self.column_formsets:
            for column_form in column_formset:
                column_form.instance.schema = schema
            column_formset.save(commit)

        return self.instance
