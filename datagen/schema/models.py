from functools import cache
from itertools import chain
from typing import Any, Iterable

from django.conf import settings
from django.contrib.auth import get_user_model
from django.core.exceptions import ValidationError
from django.core.validators import (
    MaxValueValidator,
    MinLengthValidator,
    MinValueValidator,
)
from django.db import models
from django.forms.models import model_to_dict

from .services.generator import ColumnDTO, Generator


class Schema(models.Model):
    name = models.CharField(max_length=255)
    column_separator = models.CharField(max_length=1, default=",")
    quotechar = models.CharField(max_length=1, default='"')
    user = models.ForeignKey(
        get_user_model(), on_delete=models.CASCADE, related_name="schemas"
    )
    modified = models.DateTimeField(auto_now=True)
    datasets: models.QuerySet["Dataset"]

    def __str__(self) -> str:
        return self.name

    @property
    def columns(self) -> Iterable["BaseColumn"]:
        return chain.from_iterable(
            column_model.objects.filter(schema=self)
            for column_model in BaseColumn.__subclasses__()
        )

    @property
    def columns_grouped_by_type(self) -> dict:
        return {
            column_model: column_model.objects.filter(schema=self)
            for column_model in BaseColumn.__subclasses__()
        }

    @property
    def get_generator(self) -> Generator:
        return Generator(
            ColumnDTO(
                column.name,
                column.type,
                column.order,
                column.params,
            )
            for column in self.columns
        )

    def run_generate_task(self, num_rows: int) -> None:
        from .tasks import generate_data  # prevent circular import

        dataset = self.datasets.create(num_rows=num_rows)
        if settings.INPROCESS_CELERY_WORKER:
            generate_data.run(dataset.pk)
        else:
            generate_data.delay(dataset.pk)

        return dataset


class Dataset(models.Model):
    schema = models.ForeignKey(
        Schema, on_delete=models.CASCADE, related_name="datasets"
    )
    num_rows = models.IntegerField()
    file = models.FileField(
        storage=settings.PRIVATE_MEDIA_STORAGE(), null=True
    )
    created = models.DateTimeField(auto_now_add=True)

    def __str__(self) -> str:
        return f"{self.schema.name} - {self.num_rows} rows on {self.created.strftime('%Y-%m-%d')}"


class NoColumnException(ValueError):
    pass


class BaseColumn(models.Model):
    label: str
    type: str
    name = models.CharField(max_length=255, validators=[MinLengthValidator(1)])
    order = models.IntegerField()
    schema = models.ForeignKey(Schema, on_delete=models.CASCADE)

    class Meta:
        abstract = True

    @property
    def params(self) -> dict[str, Any]:
        return model_to_dict(self, exclude=("id", "name", "order", "schema"))

    def __init_subclass__(cls) -> None:
        """Ensure `type` and `label` attributes on subclasses are set"""
        if not (type_ := getattr(cls, "type", None)):
            raise AttributeError(f"{cls.__name__} has no type specified.")
        if not getattr(cls, "label", None):  # construct label from type
            setattr(cls, "label", type_.replace("_", " ").title())

        super().__init_subclass__()

    def __str__(self) -> str:
        return f"{self.label} - {self.name}"

    @classmethod
    @cache  # Beware, cache is unlimited! Though, exception shouldn't be cached, so it's ok.
    def get_column_by_type(cls, type_):
        for column in cls.__subclasses__():
            if column.type == type_:
                return column
        raise NoColumnException(f"No column of type {type_}")


class NameColumn(BaseColumn):
    type = "name"


class RandomIntColumn(BaseColumn):
    type = "random_int"
    label = "Random integer"

    min = models.IntegerField(default=1)
    max = models.IntegerField(default=100)

    def clean(self) -> None:
        super().clean()
        if self.min > self.max:
            raise ValidationError(
                {
                    "__all__": "Min must be less than max.",
                    "min": "Min must be less than max.",
                    "max": "Max must be greater than min.",
                }
            )


class JobColumn(BaseColumn):
    type = "job"


class EmailColumn(BaseColumn):
    type = "safe_email"


class PhoneNumberColumn(BaseColumn):
    type = "phone_number"


class DomainColumn(BaseColumn):
    type = "safe_domain_name"


class CompanyColumn(BaseColumn):
    type = "company"


class AddressColumn(BaseColumn):
    type = "address"


class DateColumn(BaseColumn):
    type = "date"


class SentencesColumn(BaseColumn):
    type = "sentences_variable_str"
    label = "Sentences"

    nb_min = models.IntegerField(
        verbose_name="min",
        default=1,
        validators=[MinValueValidator(1), MaxValueValidator(100000)],
    )
    nb_max = models.IntegerField(
        verbose_name="max",
        default=1,
        validators=[MinValueValidator(1), MaxValueValidator(100000)],
    )

    def clean(self) -> None:
        super().clean()
        if self.nb_min > self.nb_max:
            raise ValidationError(
                {
                    "__all__": "Min must be less than max.",
                    "nb_min": "Min must be less than max.",
                    "nb_max": "Max must be greater than min.",
                }
            )
