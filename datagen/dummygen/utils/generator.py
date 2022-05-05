from typing import OrderedDict, List, Generator

from dataclasses import dataclass

from factory import Faker, ListFactory



class Field:
    def __init__(self, name, f_type, f_params, order) -> None:
        self.name = name
        self.f_type = f_type
        self.f_params = f_params
        self.order = order


class Schema:
    def __init__(self, fields: List) -> None:
        self._validate_fields(fields)
        self.fields = sorted(fields, key=lambda x: x.order)
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
        (f'f_{idx}', Faker(field.type, **field.params)) 
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
        
