import csv
from pathlib import Path

from .generator import Schema
from ..models import GeneratedData


def generate_to_csv(
    schema: Schema,
    num_rows: int,
    delimiter,
    quotechar,
    file_slug,
    dataset: GeneratedData,
):
    tmp_path = f"/tmp/{file_slug}"
    Path(tmp_path).parent.mkdir(
        exist_ok=True
    )  # in case worker will get non-singlethreaded

    with open(tmp_path, "w") as csv_file:
        csv_writer = csv.writer(csv_file, delimiter=delimiter, quotechar=quotechar)
        csv_writer.writerow(schema.header)
        csv_writer.writerows(schema.get_data_generator(num_rows))

    with open(tmp_path, "rb") as csv_file:
        dataset.file.save(file_slug, csv_file, save=False)
