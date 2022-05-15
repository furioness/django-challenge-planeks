from datetime import datetime

from celery import shared_task
from django.utils.text import slugify

from .models import GeneratedData
from .utils.data_saving import generate_to_csv
from .utils.generator import Schema as GenSchema


@shared_task
def generate_data(dataset_pk: int):
    dataset = GeneratedData.objects.get(pk=dataset_pk)
    schema = dataset.schema  # prefetch or already?
    gen_schema: GenSchema = schema.gen_schema_instance

    file_slug = f"{schema.user.id}/{slugify(schema.name)}_{dataset.num_records}_{datetime.isoformat(dataset.created)}.csv"

    csv_file_path = generate_to_csv(
        gen_schema.get_data_generator(dataset.num_records),
        gen_schema.header,
        schema.column_separator,
        schema.quotechar,
    )

    with open(csv_file_path, "rb") as csv_file:
        dataset.file.save(file_slug, csv_file)

    dataset.save()
