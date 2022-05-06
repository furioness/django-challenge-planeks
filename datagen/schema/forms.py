from django import forms
from .utils.field_forms import FIELD_FORMS


class SchemaForm(forms.Form):
    name = forms.CharField(max_length=255)
    column_separator = forms.CharField(max_length=1, initial=',')
    quotechar = forms.CharField(max_length=1, initial='"')
    fields_json = forms.JSONField(widget=forms.HiddenInput())
    
    
class FieldSelectForm(forms.Form):
    name = forms.CharField(max_length=255)
    f_type = forms.ChoiceField(choices=((key, key) for key in FIELD_FORMS.keys()), label='Type')
    order = forms.IntegerField(min_value=0)
    
class GenerateForm(forms.Form):
    num_rows = forms.IntegerField(min_value=1, initial=500)