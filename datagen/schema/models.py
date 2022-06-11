from django.conf import settings
from django.contrib.auth import get_user_model
from django.core.validators import MaxValueValidator, MinValueValidator
from django.db import models

from .services.generator import Schema as GenSchema


class Schema(models.Model):
    name = models.CharField(max_length=255)
    column_separator = models.CharField(max_length=1, default=",")
    quotechar = models.CharField(max_length=1, default='"')
    user = models.ForeignKey(
        get_user_model(), on_delete=models.CASCADE, related_name="schemas"
    )
    modified = models.DateTimeField(auto_now=True)

    def __str__(self):
        return self.name

    @property
    def columns(self):
        columns = []
        for column_model in BaseColumn.__subclasses__():
            columns.extend(column_model.objects.filter(schema=self))
        return columns

    @property
    def columns_grouped_by_type(self):
        return [
            (column_model, column_model.objects.filter(schema=self))
            for column_model in BaseColumn.__subclasses__()
        ]

    @property
    def gen_schema_instance(self) -> GenSchema:

        return GenSchema.from_dict_list(self.columns)

    def get_field_forms(self):
        return [
            get_form_for_field(field)
            for field in self.gen_schema_instance.fields
        ]

    def run_generate_task(self, num_rows: int):
        from .tasks import generate_data  # prevent circular import

        dataset = self.datasets.create(num_rows=num_rows)  # type: ignore
        if settings.INPROCESS_CELERY_WORKER:
            generate_data.run(dataset.id)
        else:
            generate_data.delay(dataset.pk)


class Dataset(models.Model):
    schema = models.ForeignKey(
        Schema, on_delete=models.CASCADE, related_name="datasets"
    )
    num_rows = models.IntegerField()
    file = models.FileField(
        storage=settings.PRIVATE_MEDIA_STORAGE(), null=True
    )
    created = models.DateTimeField(auto_now_add=True)


class BaseColumn(models.Model):
    type = None
    label = None
    order = models.IntegerField(default=1)
    name = models.CharField(max_length=255)
    schema = models.ForeignKey(Schema, on_delete=models.CASCADE)

    class Meta:
        abstract = True


class NameColumn(BaseColumn):
    type = "name"
    label = "Name"


class RandomIntColumn(BaseColumn):
    type = "random_int"
    label = "Random integer"

    min = models.IntegerField(
        help_text='Min', default=1, validators=[MinValueValidator(-9999999)]
    )
    max = models.IntegerField(
        help_text="Max", default=100, validators=[MaxValueValidator(9999999)]
    )
