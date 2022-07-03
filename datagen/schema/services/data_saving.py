import csv
import uuid
from pathlib import Path
from typing import Iterable


def generate_to_csv(
    generator: Iterable, header: list[str], delimiter: str, quotechar: str
) -> Path:
    tmp_path = Path(f"/tmp/{uuid.uuid4()}")

    with open(tmp_path, "w") as csv_file:
        csv_writer = csv.writer(
            csv_file, delimiter=delimiter, quotechar=quotechar
        )
        csv_writer.writerow(header)
        csv_writer.writerows(generator)

    return tmp_path
