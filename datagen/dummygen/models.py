import imp
from django.db import models
from django.contrib.auth import get_user_model
from utils.generator import Schema as GenSchema


class Schema(models.Model):
    name = models.CharField(max_length=255)
    user = models.ForeignKey(get_user_model(), on_delete=models.CASCADE)
    fields = models.JSONField()

    def __str__(self):
        return self.name
    
    @property
    def gen_schema_instance(self) -> GenSchema:
        if not hasattr(self, '_gen_schema_instance'):
            self._gen_schema_instance = GenSchema.from_JSON(self.fields)
        return self._gen_schema_instance
    
    def get_field_forms(self):
        self.gen_schema_instance.to_forms()
        
class GeneratedData(models.Model):
    schema = models.ForeignKey(Schema, on_delete=models.RESTRICT)
    num_records = models.IntegerField()
    slug = models.URLField()
    