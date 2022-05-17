from django.contrib.auth import get_user_model
from django.db import models
from django.conf import settings

from .forms.field_forms import get_form_for_field
from .utils.generator import Schema as GenSchema


class Schema(models.Model):
    name = models.CharField(max_length=255)
    column_separator = models.CharField(max_length=1, default=",")
    quotechar = models.CharField(max_length=1, default='"')
    user = models.ForeignKey(get_user_model(), on_delete=models.CASCADE, related_name="schemas")
    fields = models.JSONField()

    def __str__(self):
        return self.name

    @property
    def gen_schema_instance(self) -> GenSchema:
        if not hasattr(self, "_gen_schema_instance"):
            self._gen_schema_instance = GenSchema.from_dict_list(self.fields)
        return self._gen_schema_instance

    def get_field_forms(self):
        return [get_form_for_field(field) for field in self.gen_schema_instance.fields]

    def run_generate_task(self, num_rows: int):
        from .tasks import generate_data  # prevent circular import

        dataset = self.generated_data.create(num_rows=num_rows)  # type: ignore
        if settings.INPROCESS_CELERY_WORKER:
            generate_data.run(dataset.id)
        else:
            generate_data.delay(dataset.pk)


class GeneratedData(models.Model):
    schema = models.ForeignKey(Schema, on_delete=models.CASCADE, related_name="generated_data")
    num_rows = models.IntegerField()
    file = models.FileField(storage=settings.PRIVATE_MEDIA_STORAGE(), null=True)
    created = models.DateTimeField(auto_now_add=True)
