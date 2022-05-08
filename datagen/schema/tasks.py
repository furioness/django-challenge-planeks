from datetime import datetime

from celery import shared_task

from .models import GeneratedData
from .utils.data_saving import generate_to_csv


@shared_task
def generate_data(dataset_pk: int):
    dataset = GeneratedData.objects.get(pk=dataset_pk)
    schema = dataset.schema  # prefetch or already?
    schema_gen = schema.gen_schema_instance

    file_slug = f'{schema.user.id}/{schema.name.replace(" ", "-")}_{schema.num_rows}_{datetime.isoformat(datetime.now())}.csv'

    
    
    generate_to_csv(schema_gen, dataset.num_rows, schema.column_separator, schema.quotechar, file_slug, dataset)
    
    dataset.generation_complete=True
    dataset.save()
