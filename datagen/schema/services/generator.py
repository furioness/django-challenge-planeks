from dataclasses import dataclass
from typing import OrderedDict, List, Generator as GeneratorType, Iterable

from factory import Faker, ListFactory


@dataclass
class ColumnDTO:
    name: str
    type: str
    order: int
    params: dict


class Generator:
    def __init__(self, columns: Iterable[ColumnDTO]):
        self.fields = sorted(columns, key=lambda x: x.order)
        self.header: list[str] = [field.name for field in self.fields]

    def _get_Factory(self) -> ListFactory:  # NOSONAR
        key_values = [
            (f"f_{idx}", Faker(field.type, **field.params))
            for idx, field in enumerate(self.fields)
        ]
        return type("_Factory", (ListFactory,), OrderedDict(key_values))  # type: ignore

    def data_generator(
        self, num_records: int
    ) -> GeneratorType[List, None, None]:
        factory = self._get_Factory()
        for _ in range(num_records):
            yield factory()  # type: ignore
