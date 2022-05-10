from typing import OrderedDict, List, Generator
import json

from factory import Faker, ListFactory


class Field:
    def __init__(self, name, f_type, f_params, order) -> None:
        self.name = name
        self.f_type = f_type
        self.f_params = f_params
        self.order = order

    def __str__(self) -> str:
        return f"Field(name={self.name}, f_type={self.f_type}, f_params={self.f_params}, order={self.order})"

    def to_dict(self):
        return {
            "name": self.name,
            "f_type": self.f_type,
            "f_params": self.f_params,
            "order": self.order,
        }

    @staticmethod
    def from_dict(field_dict: dict) -> "Field":
        return Field(**field_dict)


class Schema:
    def __init__(self, fields: List[Field]) -> None:
        self._validate_fields(fields)
        self.fields = sorted(fields, key=lambda x: x.order)
        self.header = [field.name for field in self.fields]

    @staticmethod
    def _validate_fields(fields: List) -> None:
        unique_names = set()
        for field in fields:
            if field.name in unique_names:
                raise ValueError(f"Duplicate field name: {field.name}")
            unique_names.add(field.name)
            #  validate allowed types and type-params

    def _get_generator(self) -> ListFactory:
        key_values = [
            (f"f_{idx}", Faker(field.f_type, **field.f_params))
            for idx, field in enumerate(self.fields)
        ]
        return type("_Factory", (ListFactory,), OrderedDict(key_values))  # type: ignore

    def get_data_generator(self, num_records: int) -> Generator[List, None, None]:
        generator = self._get_generator()
        for _ in range(num_records):
            yield generator()  # type: ignore

    def to_JSON(self) -> str:
        return json.dumps([field.to_dict() for field in self.fields])

    @staticmethod
    def from_JSON(fields_json: str):
        fields = json.loads(fields_json)
        return Schema([Field.from_dict(field) for field in fields])

    @staticmethod
    def from_dict_list(fields_dict: List[dict]) -> "Schema":
        return Schema([Field.from_dict(field) for field in fields_dict])
