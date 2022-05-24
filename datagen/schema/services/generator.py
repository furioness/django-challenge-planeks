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


class Schema:
    def __init__(self, fields: List[Field]) -> None:
        self.fields = sorted(fields, key=lambda x: x.order)
        self.header: list[str] = [field.name for field in self.fields]

    def _get_Factory(self) -> ListFactory:
        key_values = [
            (f"f_{idx}", Faker(field.f_type, **field.f_params))
            for idx, field in enumerate(self.fields)
        ]
        return type("_Factory", (ListFactory,), OrderedDict(key_values))  # type: ignore

    def data_generator(self, num_records: int) -> Generator[List, None, None]:
        factory = self._get_Factory()
        for _ in range(num_records):
            yield factory()  # type: ignore

    def to_JSON(self) -> str:
        return json.dumps([field.to_dict() for field in self.fields])

    @staticmethod
    def from_dict_list(fields_dict: List[dict]) -> "Schema":
        return Schema([Field(**field) for field in fields_dict])
