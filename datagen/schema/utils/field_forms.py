from django import forms

from .generator import Field


class BaseFieldForm(forms.Form):
    label = ''
    type = ''
    f_params = ()
    
    f_type = forms.CharField(initial='',  widget=forms.HiddenInput())
    name = forms.CharField(label='Column name', max_length=100, required=True)
    order = forms.IntegerField(label='Order', min_value=0, required=True)
    
    # def __new__(cls, *args, **kwargs):
    #     res = object.__new__(cls)
    #     if not res.f_type:
    #         raise NotImplementedError('f_type is not set')
    #     res.base_fields['type'].initial = cls.f_type
    #     return res
    
    def __init__(self, data=None, *args, **kwargs):
        if not self.type:
            raise NotImplementedError('type is not set')
        if not self.label:
            raise NotImplementedError('label is not set')
        
        self.base_fields['f_type'].initial = self.type
        if data:
            params = data.pop('f_params', {})
            data.update(params)
        super().__init__(data, *args, **kwargs)
        
        
    def to_schema_field(self):
        return Field(name=self.cleaned_data['name'], 
                     f_type=self.type, 
                     f_params=self.get_params(), 
                     order=self.cleaned_data['order'])
        
    def get_params(self) -> dict:
        return {param: self.cleaned_data[param] for param in self.f_params}
    
class FullNameFieldForm(BaseFieldForm):
    type = 'name'
    label = 'Name'
    
class RandomIntFieldForm(BaseFieldForm):
    type = 'random_int'
    label = 'Random integer'
    f_params = ('min', 'max')
    
    min = forms.IntegerField(label='Min', min_value=-9999999, max_value=9999999, required=True)
    max = forms.IntegerField(label='Max', min_value=-9999999, max_value=9999999, required=True)
    
    
    def clean(self):
        cleaned_data = super().clean()
        min_ = cleaned_data.get('min')  # type: ignore
        max_ = cleaned_data.get('max')  # type: ignore
        if min_ > max_:  # type: ignore
            raise forms.ValidationError('Min must be less than max')
        
        return cleaned_data

    
FIELD_FORMS = {
        'name': FullNameFieldForm,
        'random_int': RandomIntFieldForm
    }
 
def get_form_for_field(field: Field):
    return FIELD_FORMS[field.f_type](data={
            'name': field.name, 
            'order': field.order,
            **field.f_params
            })
    
def get_form_for_dict_field(field: dict):
    return FIELD_FORMS[field['f_type']](data={
            'name': field['name'], 
            'order': field['order'],
            **field['f_params']
            })
