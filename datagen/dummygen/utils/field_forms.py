from abc import ABC
from django import forms

from .generator import Field


class BaseFieldForm(ABC, forms.Form):
    name = forms.CharField(label='Column name', max_length=100)
    order = forms.IntegerField(label='Order', min_value=0)
    
    def to_schema_field(self):
        raise NotImplementedError()
    
    
class NameFieldForm(BaseFieldForm):
    type = forms.ChoiceField(label='Type', 
        choices=[
            ('name', 'Name'), 
            ('first_name', 'First name'),
            ('last_name', 'Last name'),
        ]
    )
    def to_schema_field(self):
        return Field(name=self.cleaned_data['name'], 
                     f_type=self.cleaned_data['type'], 
                     f_params={}, 
                     order=self.cleaned_data['order'])
    
class RandomIntegerFieldForm(BaseFieldForm):
    min = forms.IntegerField(label='Min', min_value=-9999999, max_value=9999999)
    max = forms.IntegerField(label='Max', min_value=-9999999, max_value=9999999)
    
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
    
    