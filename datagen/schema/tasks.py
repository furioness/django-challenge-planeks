import os
from datetime import datetime

from celery import shared_task
from django.utils.text import slugify

from .models import Dataset, Schema
from .services.data_saving import generate_to_csv
from .services.generator import Schema as GenSchema


@shared_task
def generate_data(dataset_pk: int):
    dataset: Dataset = Dataset.objects.select_related("schema").get(
        pk=dataset_pk
    )
    schema: Schema = dataset.schema
    gen_schema: GenSchema = schema.gen_schema_instance

    file_slug = f"{schema.user.id}/{slugify(schema.name)}_{dataset.num_rows}_{datetime.isoformat(dataset.created)}.csv"

    csv_file_path = generate_to_csv(
        gen_schema.data_generator(dataset.num_rows),
        gen_schema.header,
        schema.column_separator,
        schema.quotechar,
    )

    with open(csv_file_path, "rb") as csv_file:
        dataset.file.save(file_slug, csv_file)

    dataset.save()
    os.remove(csv_file_path)
