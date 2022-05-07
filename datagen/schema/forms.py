from django import forms

from .utils.field_forms import FIELD_FORMS
from .models import Schema as SchemaModel


class SchemaForm(forms.ModelForm):
    class Meta:
        model = SchemaModel
        fields = ('name', 'column_separator', 'quotechar', 'fields')
        
    name = forms.CharField(max_length=255)
    column_separator = forms.CharField(max_length=1, initial=',')
    quotechar = forms.CharField(max_length=1, initial='"')
    fields = forms.JSONField(widget=forms.HiddenInput())  # type: ignore
    fieldFormsTemplates = FIELD_FORMS
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.field_forms = []
        if 'instance' in kwargs:
            self._init_field_forms(self.instance.fields)
        
    def clean_fields(self):
        try:
            self._init_field_forms(self.cleaned_data['fields'])
        except Exception as e:
            print(e)
            self.add_error('fields', 'Error parsing fields')
            return 
        
        if not len(self.field_forms):
            self.add_error('fields', 'No fields found')
            return
        
        if not all(form.is_valid() for form in self.field_forms):
             self.add_error(None, 'Invalid fields')
             
        return [form.to_schema_field().to_dict() for form in self.field_forms]
    
    def _init_field_forms(self, fields):
        if fields:
            self.field_forms = [FIELD_FORMS[field['f_type']](field) for field in fields]
             
    
class FieldSelectForm(forms.Form):
    name = forms.CharField(max_length=255)
    type = forms.ChoiceField(choices=((key, key) for key in FIELD_FORMS.keys()), label='Type')
    order = forms.IntegerField(min_value=0)
    f_type = forms.ChoiceField(choices=((key, key) for key in FIELD_FORMS.keys()), label='Type')
    order = forms.IntegerField(min_value=0)
    
class GenerateForm(forms.Form):
    num_rows = forms.IntegerField(label='Number of rows', min_value=1, initial=500000)
