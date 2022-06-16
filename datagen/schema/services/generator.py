from typing import OrderedDict, List, Generator

from factory import Faker, ListFactory


class Field:
    def __init__(self, name: str, type: str, order: int, params: dict):
        self.name = name
        self.type = type
        self.order = order
        self.params = params

    def __str__(self):
        return f"Field(name={self.name}, f_type={self.type}, f_params={self.params}, order={self.order})"


class Schema:
    def __init__(self, fields: List[Field]):
        self.fields = sorted(fields, key=lambda x: x.order)
        self.header: list[str] = [field.name for field in self.fields]

    def _get_Factory(self) -> ListFactory:  # NOSONAR
        key_values = [
            (f"f_{idx}", Faker(field.type, **field.params))
            for idx, field in enumerate(self.fields)
        ]
        return type("_Factory", (ListFactory,), OrderedDict(key_values))  # type: ignore

    def data_generator(self, num_records: int) -> Generator[List, None, None]:
        factory = self._get_Factory()
        for _ in range(num_records):
            yield factory()  # type: ignore

    @staticmethod
    def from_dict_list(fields: list[tuple[str, str, int, dict]]) -> "Schema":
        return Schema(
            [
                Field(name, type, order, params)
                for name, type, order, params in fields
            ]
        )
