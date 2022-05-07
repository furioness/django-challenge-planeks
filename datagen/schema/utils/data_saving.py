import csv
from pathlib import Path

from .generator import Schema


def generate_to_csv(schema: Schema, num_rows: int, delimiter, quotechar, filename):
    Path(filename).parent.mkdir(parents=True, exist_ok=True)
    with open(filename, 'w') as csv_file:
        csv_writer = csv.writer(csv_file,
                                delimiter=delimiter, 
                                quotechar=quotechar)
        csv_writer.writerow(schema.header)
        csv_writer.writerows(schema.get_data_generator(num_rows))
