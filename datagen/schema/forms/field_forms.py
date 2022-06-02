from django import forms

from ..services.generator import Field


class BaseFieldForm(forms.Form):
    label: str
    type: str
    f_params: tuple

    f_type = forms.CharField(initial="", widget=forms.HiddenInput())
    name = forms.CharField(label="Column name", max_length=100, required=True)
    order = forms.IntegerField(label="Order", min_value=0, required=True)

    def __new__(cls, *args, **kwargs):
        if not hasattr(cls, "type"):
            raise ValueError("BaseFieldForm has no type specified.")
        if not hasattr(cls, "label"):
            label = cls.type.replace("_", " ")
            cls.label = label[0].title() + label[1:]
        if not hasattr(cls, "f_params"):
            #  look for base fields as Field metaclass moves from class own
            cls.f_params = tuple(
                field
                for field in cls.base_fields
                if field not in BaseFieldForm.base_fields
            )
        cls.base_fields["f_type"].initial = cls.type

        # put the Order field at the end
        fields = list(cls.base_fields.keys())
        fields.remove("order")
        cls.field_order = fields + ["order"]

        return object.__new__(cls)

    def __init__(self, data=None, *args, **kwargs):
        if data:
            params = data.pop("f_params", {})
            data.update(params)
        super().__init__(data, *args, **kwargs)

    def to_schema_field(self):
        return Field(
            name=self.cleaned_data["name"],
            f_type=self.type,
            f_params=self._get_params(),
            order=self.cleaned_data["order"],
        )

    def _get_params(self) -> dict:
        return {param: self.cleaned_data[param] for param in self.f_params}


class MinmaxValidationMixin:
    def validate_minmax(self, min_field, max_field):
        min_ = self.cleaned_data[min_field]
        max_ = self.cleaned_data[max_field]
        if min_ > max_:  # type: ignore
            self.add_error(min_field, "Min value must be less than max value")  # type: ignore
            self.add_error(max_field, "Max value must be greater than min value")  # type: ignore
            raise forms.ValidationError("Min must be less than max")


class FullNameFieldForm(BaseFieldForm):
    type = "name"


class RandomIntFieldForm(MinmaxValidationMixin, BaseFieldForm):
    type = "random_int"
    label = "Random integer"

    min = forms.IntegerField(
        label="Min", min_value=-9999999, initial=1, max_value=9999999
    )
    max = forms.IntegerField(
        label="Max", min_value=-9999999, initial=100, max_value=9999999
    )

    def clean(self):
        cleaned_data = super().clean()
        self.validate_minmax("min", "max")

        return cleaned_data


class JobFieldForm(BaseFieldForm):
    type = "job"


class EmailFieldForm(BaseFieldForm):
    type = "safe_email"


class PhoneNumberFieldForm(BaseFieldForm):
    type = "phone_number"


class DomainFieldForm(BaseFieldForm):
    type = "safe_domain_name"


class CompanyFieldForm(BaseFieldForm):
    type = "company"


class AddressFieldForm(BaseFieldForm):
    type = "address"


class DateFieldForm(BaseFieldForm):
    type = "date"


class SentencesFieldForm(MinmaxValidationMixin, BaseFieldForm):
    type = "sentences_variable_str"
    label = "Sentences"

    nb_min = forms.IntegerField(
        min_value=1, initial=1, max_value=100000, label="Min sentences"
    )
    nb_max = forms.IntegerField(
        min_value=1, initial=5, max_value=100000, label="Min sentences"
    )

    # ext_word_list = forms.CharField(
    #     label='Custom words (comma separated)',
    #     required=False,
    #     validators=[lambda str: [word.strip() for word in str.split(',')]]
    # )

    def clean(self):
        cleaned_data = super().clean()
        self.validate_minmax("nb_min", "nb_max")

        return cleaned_data


FIELD_FORMS = {
    field_form.type: field_form
    for field_form in BaseFieldForm.__subclasses__()
}

# a temporal hack to init (call __new__) labels and stuff. Probably fixable by metaclasses.
[form() for form in FIELD_FORMS.values()]


def get_form_for_field(field: Field):
    return FIELD_FORMS[field.f_type](
        data={"name": field.name, "order": field.order, **field.f_params}
    )
