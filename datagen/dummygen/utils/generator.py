from os import stat
from pkgutil import ImpImporter
from typing import OrderedDict, List, Generator
from dataclasses import dataclass
import json

from factory import Faker, ListFactory

from .field_forms import NameFieldForm, RandomIntegerFieldForm




class Field:
    FIELD_FORMS = {
        'name': NameFieldForm,
        'random_integer': RandomIntegerFieldForm
    }
    
    def __init__(self, name, f_type, f_params, order) -> None:
        self.name = name
        self.f_type = f_type
        self.f_params = f_params
        self.order = order
        
    def to_form(self):
        return self.FIELD_FORMS[self.f_type]({
            'name': self.name, 
            'order': self.order,
            **self.f_params
            })
        
    def to_dict(self):
        return {
            'name': self.name,
            'f_type': self.f_type, 
            'f_params': self.f_params,
            'order': self.order,
            }
        
    @staticmethod
    def from_dict(field_dict: dict) -> 'Field':
        return Field(**field_dict)        


class Schema:
    def __init__(self, fields: List) -> None:
        self._validate_fields(fields)
        self.fields: List[Field] = sorted(fields, key=lambda x: x.order)
        self.header = [field.name for field in self.fields]
    
    @staticmethod
    def _validate_fields(fields: List) -> None:
        unique_names = set()
        for field in fields:
            if field.name in unique_names:
                raise ValueError(f'Duplicate field name: {field.name}')
            unique_names.add(field.name)
            #  validate allowed types and type-params
    
    def _get_generator(self) -> ListFactory:
        key_values = [
        (f'f_{idx}', Faker(field.f_type, **field.f_params)) 
               for idx, field in enumerate(self.fields)
        ]
        return type('Schema', 
                    (ListFactory, ), 
                    OrderedDict(key_values)
                )  # type: ignore

    def generate_data(self, num_records: int) -> Generator[List, None, None]:
        generator = self._get_generator()
        for _ in range(num_records):
            yield generator()  # type: ignore
            
    def to_JSON(self) -> str:
        return json.dumps(field.to_dict() for field in self.fields)
    
    @staticmethod    
    def from_JSON(fields_json: str):
        fields = json.loads(fields_json)
        return Schema([Field.from_dict(field) for field in fields])
