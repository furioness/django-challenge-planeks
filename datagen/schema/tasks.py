from datetime import datetime

from celery import shared_task
from django.conf import settings

from .utils.data_saving import generate_to_csv
from .models import Schema

@shared_task
def generate_data(schema_pk: int, num_rows: int):
    schema = Schema.objects.get(pk=schema_pk)
    schema_gen = schema.gen_schema_instance

    filename = f'{schema.name}_{num_rows}_{datetime.isoformat(datetime.now())}.csv'
    slug = f'{schema.user.id}/{filename}'
    filepath = f'{settings.MEDIA_ROOT}/{slug}'
    
    gen_data_db_inst = schema.generated_data.create(num_records=num_rows, slug=slug)
    
    generate_to_csv(schema_gen, num_rows, schema.column_separator, schema.quotechar, filepath)
    
    gen_data_db_inst.generation_complete=True
    gen_data_db_inst.save()
