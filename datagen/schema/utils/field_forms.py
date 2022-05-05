from distutils.command.clean import clean
from django import forms

from .generator import Field


class BaseFieldForm(forms.Form):
    name = forms.CharField(label='Column name', max_length=100, required=True)
    order = forms.IntegerField(label='Order', min_value=0, required=True)
    f_type = None
    
    def to_schema_field(self):
        raise NotImplementedError()
    
    
class NameFieldForm(BaseFieldForm):
    f_type = forms.ChoiceField(label='Type', 
        choices=[
            ('name', 'Name'), 
            ('first_name', 'First name'),
            ('last_name', 'Last name'),
        ], 
        initial='name',
        required=True
    )
    def to_schema_field(self):
        return Field(name=self.cleaned_data['name'], 
                     f_type=self.cleaned_data['f_type'], 
                     f_params={}, 
                     order=self.cleaned_data['order'])
    
class RandomIntegerFieldForm(BaseFieldForm):
    min = forms.IntegerField(label='Min', min_value=-9999999, max_value=9999999, required=True)
    max = forms.IntegerField(label='Max', min_value=-9999999, max_value=9999999, required=True)
    f_type = forms.CharField(initial='random_integer', widget=forms.HiddenInput(), required=True)
    
    def clean(self):
        cleaned_data = super().clean()
        min_ = cleaned_data.get('min')  # type: ignore
        max_ = cleaned_data.get('max')  # type: ignore
        if min_ > max_:  # type: ignore
            raise forms.ValidationError('Min must be less than max')
        
        return cleaned_data
    
    def to_schema_field(self):
        return Field(name=self.cleaned_data['name'], 
                     f_type='random_integer', 
                     f_params={
                         'min': self.cleaned_data['min'], 
                         'max': self.cleaned_data['max']
                         }, 
                     order=self.cleaned_data['order'])
    
FIELD_FORMS = {
        'name': NameFieldForm,
        'random_integer': RandomIntegerFieldForm
    }
 
def get_form_for_field(field: Field):
    return FIELD_FORMS[field.f_type](data={
            'name': field.name, 
            'order': field.order,
            **field.f_params
            })
