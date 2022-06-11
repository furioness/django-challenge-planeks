from django import forms 
from django.conf import settings
from django.db.models import Sum

from .models import Dataset, BaseColumn


class GenerateForm(forms.Form):
    num_rows = forms.IntegerField(label="Rows", min_value=1, initial=1234)

    def __init__(self, *args, **kwargs):
        self.user = kwargs.pop("request").user
        super().__init__(*args, **kwargs)

    def clean_num_rows(self):
        num_rows = self.cleaned_data["num_rows"]
        if not self.user.has_perm("schema.unlimited_generation"):
            rows_used = (
                Dataset.objects.filter(
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
    
class FieldSelectForm(forms.Form):
    name = forms.CharField(max_length=255)
    type = forms.ChoiceField(
        choices=((Column.__name__, Column.label) for Column in BaseColumn.__subclasses__()),
        label="Type",
    )
    order = forms.IntegerField()