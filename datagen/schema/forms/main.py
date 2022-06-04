from django import forms
from django.conf import settings
from django.db.models import Sum

from ..models import Schema as SchemaModel, GeneratedData as GeneratedDataModel
from .field_forms import FIELD_FORMS


class SchemaForm(forms.ModelForm):
    class Meta:
        model = SchemaModel
        fields = ("name", "column_separator", "quotechar", "fields")

    fields = forms.JSONField(widget=forms.HiddenInput(), error_messages={"required": "Please add some fields."})  # type: ignore
    fieldFormsTemplates = FIELD_FORMS

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        if "instance" in kwargs:
            self._init_field_forms(self.instance.fields)

    def clean_fields(self):
        is_valid = (
            True  # to allow check for multiple errors before early return
        )
        try:
            self._init_field_forms(self.cleaned_data["fields"])
        except Exception as e:
            # TODO: add logging for suspicious erroneous input
            self.add_error("fields", "Error parsing fields.")
            return

        if not all(form.is_valid() for form in self.field_forms):
            self.add_error("fields", "Invalid fields.")
            is_valid = False

        duplicate_names, duplicate_forms = self._get_duplicate_fields()
        if duplicate_names:
            self.add_error(
                "fields",
                f"Duplicate field names: {', '.join(duplicate_names)}",
            )
            for field in duplicate_forms:
                field.add_error("name", "Duplicate field name.")
            return

        if is_valid:
            return [
                form.to_schema_field().to_dict() for form in self.field_forms
            ]

    def _get_duplicate_fields(self):
        names = {}
        for field in self.field_forms:
            names.setdefault(field.cleaned_data["name"], []).append(field)
        duplicate_forms = []
        duplicate_names = []
        for name, forms in names.items():
            if len(forms) > 1:
                duplicate_forms += forms
                duplicate_names.append(name)

        return duplicate_names, duplicate_forms

    def _init_field_forms(self, fields):
        self.field_forms = (
            []
        )  # make sure to not get duplicates as this function can be called twice - in case of POSTing from Update view

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
    num_rows = forms.IntegerField(label="Rows", min_value=1, initial=1234)

    def __init__(self, *args, **kwargs):
        self.user = kwargs.pop("request").user
        super().__init__(*args, **kwargs)

    def clean_num_rows(self):
        num_rows = self.cleaned_data["num_rows"]
        if not self.user.has_perm("schema.unlimited_generation"):
            rows_used = (
                GeneratedDataModel.objects.filter(
                    schema__user=self.user
                ).aggregate(Sum("num_rows"))["num_rows__sum"]
                or 0
            )
            rows_left = settings.USER_GENERATION_ROW_LIMIT - rows_used

            if num_rows > rows_left:
                raise forms.ValidationError(
                    f"You have {rows_left} rows left. Please reduce the number of rows to {rows_left} or less."
                )

        return num_rows
