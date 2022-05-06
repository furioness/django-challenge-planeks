from distutils.ccompiler import gen_lib_options
from django.db import models
from django.contrib.auth import get_user_model

from .utils.generator import Schema as GenSchema
from .utils.field_forms import get_form_for_field


class Schema(models.Model):
    name = models.CharField(max_length=255)
    column_separator = models.CharField(max_length=1, default=',')
    quotechar = models.CharField(max_length=1, default='"')
    user = models.ForeignKey(get_user_model(), on_delete=models.CASCADE, related_name='schemas')
    fields_json = models.JSONField()

    def __str__(self):
        return self.name
    
    @property
    def gen_schema_instance(self) -> GenSchema:
        if not hasattr(self, '_gen_schema_instance'):
            self._gen_schema_instance = GenSchema.from_dict_list(self.fields_json)
        return self._gen_schema_instance
    
    def get_field_forms(self):
        return [get_form_for_field(field) 
                for field in self.gen_schema_instance.fields]
        
    def run_generate_task(self, num_rows: int):
        from .tasks import generate_data
        generate_data.delay(self, num_rows)
              
        
class GeneratedData(models.Model):
    schema = models.ForeignKey(Schema, on_delete=models.RESTRICT, related_name='generated_data')
    num_records = models.IntegerField()
    slug = models.URLField()
    generation_complete = models.BooleanField(default=False)
    