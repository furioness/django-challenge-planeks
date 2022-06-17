from itertools import chain

from django.conf import settings
from django.contrib.auth import get_user_model
from django.core.exceptions import ValidationError
from django.core.validators import MinLengthValidator
from django.db import models
from django.core.validators import MinValueValidator, MaxValueValidator
from django.forms.models import model_to_dict

from .services.generator import Generator, ColumnDTO


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
                model_to_dict(
                    column, exclude=("id", "name", "order", "schema")
                ),
            )
            for column in self.columns
        )

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


class CheckAttrsMeta(type(models.Model)):
    """Ensure that non-abstract children models
    have `label` and `type` attributes set.
    """

    def __new__(metacls, name, bases, namespace, **kwargs):  # type: ignore
        if getattr(namespace.get("Meta"), "abstract", False):
            return super().__new__(metacls, name, bases, namespace, **kwargs)

        if not namespace.get("type", None):
            raise AttributeError(f"{name} has no type specified.")
        if not namespace.get("label", None):  # construct label from type
            namespace["label"] = namespace["type"].replace("_", " ").title()

        return super().__new__(metacls, name, bases, namespace, **kwargs)


class BaseColumn(models.Model, metaclass=CheckAttrsMeta):
    label: str
    type: str
    name = models.CharField(max_length=255, validators=[MinLengthValidator(1)])
    order = models.IntegerField(default=1)
    schema = models.ForeignKey(Schema, on_delete=models.CASCADE)

    class Meta:
        abstract = True


class NameColumn(BaseColumn):
    type = "name"


class RandomIntColumn(BaseColumn):
    type = "random_int"
    label = "Random integer"

    min = models.IntegerField(default=1)
    max = models.IntegerField(default=100)

    def clean(self):
        super().clean()
        if self.min > self.max:
            raise ValidationError(
                {
                    "__all__": "Min must be less than max.",
                    "min": "Min must be less than max.",
                    "max": "Max must be greater than min.",
                }
            )


class JobFieldForm(BaseColumn):
    type = "job"


class EmailFieldForm(BaseColumn):
    type = "safe_email"


class PhoneNumberFieldForm(BaseColumn):
    type = "phone_number"


class DomainFieldForm(BaseColumn):
    type = "safe_domain_name"


class CompanyFieldForm(BaseColumn):
    type = "company"


class AddressFieldForm(BaseColumn):
    type = "address"


class DateFieldForm(BaseColumn):
    type = "date"


class SentencesFieldForm(BaseColumn):
    type = "sentences_variable_str"
    label = "Sentences"

    nb_min = models.IntegerField(
        default=1, validators=[MinValueValidator(1), MaxValueValidator(100000)]
    )
    nb_max = models.IntegerField(
        default=1, validators=[MinValueValidator(1), MaxValueValidator(100000)]
    )

    def clean(self):
        super().clean()
        if self.nb_min > self.nb_max:
            raise ValidationError(
                {
                    "__all__": "Min must be less than max.",
                    "min": "Min must be less than max.",
                    "max": "Max must be greater than min.",
                }
            )
