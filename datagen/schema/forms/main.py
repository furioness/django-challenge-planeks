from django import forms

from ..models import Schema as SchemaModel
from .field_forms import FIELD_FORMS


class SchemaForm(forms.ModelForm):
    class Meta:
        model = SchemaModel
        fields = ("name", "column_separator", "quotechar", "fields")

    name = forms.CharField(max_length=255)
    column_separator = forms.CharField(max_length=1, initial=",")
    quotechar = forms.CharField(max_length=1, initial='"')
    fields = forms.JSONField(widget=forms.HiddenInput())  # type: ignore
    fieldFormsTemplates = FIELD_FORMS

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.field_forms = []
        if "instance" in kwargs:
            self._init_field_forms(self.instance.fields)

    def clean_fields(self):
        try:
            self._init_field_forms(self.cleaned_data["fields"])
        except Exception as e:
            print(e)
            self.add_error("fields", "Error parsing fields")
            return

        if not len(self.field_forms):
            self.add_error("fields", "No fields found")
            return

        if not all(form.is_valid() for form in self.field_forms):
            self.add_error(None, "Invalid fields")
            return

        duplicates = self._get_duplicate_names()
        if duplicates:
            self.add_error(
                None, f"Duplicate field names: {', '.join(duplicates)}"
            )
            return

        return [form.to_schema_field().to_dict() for form in self.field_forms]

    def _get_duplicate_names(self):
        unique_names = set()
        duplicates = []
        for field_name in [
            field.cleaned_data["name"] for field in self.field_forms
        ]:
            if field_name in unique_names:
                duplicates.append(field_name)
                continue
            unique_names.add(field_name)
        return duplicates

    def _init_field_forms(self, fields):
        self.field_forms = []

        if not fields:
            return

        for field in fields:
            form = FIELD_FORMS[field["f_type"]](field)
            self.field_forms.append(form)


class FieldSelectForm(forms.Form):
    name = forms.CharField(max_length=255)
    type = forms.ChoiceField(
        choices=((type, form.label) for type, form in FIELD_FORMS.items()),
        label="Type",
    )
    order = forms.IntegerField(min_value=0)


class GenerateForm(forms.Form):
    num_rows = forms.IntegerField(label="Rows", min_value=1, initial=12345)