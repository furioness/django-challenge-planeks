from datetime import datetime

from celery import shared_task

from .models import Schema
from .utils.data_saving import generate_to_csv


@shared_task
def generate_data(schema_pk: int, num_rows: int):
    schema = Schema.objects.get(pk=schema_pk)
    schema_gen = schema.gen_schema_instance

    file_slug = f'{schema.user.id}/{schema.name.replace(" ", "-")}_{num_rows}_{datetime.isoformat(datetime.now())}.csv'

    dataset = schema.generated_data.create(num_records=num_rows)
    
    generate_to_csv(schema_gen, num_rows, schema.column_separator, schema.quotechar, file_slug, dataset)
    
    dataset.generation_complete=True
    dataset.save()
