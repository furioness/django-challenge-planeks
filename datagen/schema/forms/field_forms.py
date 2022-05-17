from django import forms

from ..utils.generator import Field


class BaseFieldForm(forms.Form):
    label: str
    type: str
    f_params: tuple

    f_type = forms.CharField(initial="", widget=forms.HiddenInput())
    name = forms.CharField(label="Column name", max_length=100, required=True)
    order = forms.IntegerField(label="Order", min_value=0, required=True)

    def __new__(cls, *args, **kwargs):
        if not hasattr(cls, "type"):
            raise NotImplementedError("type is not set")
        if not hasattr(cls, "label"):
            label = cls.type.replace("_", " ")
            cls.label = label[0].title() + label[1:]
        if not hasattr(cls, "f_params"):
            #  look for base fields as Field metaclass moves from class own
            cls.f_params = tuple(
                field for field in cls.base_fields if field not in ("f_type", "name", "order")
            )
        cls.base_fields["f_type"].initial = cls.type
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
            f_params=self.get_params(),
            order=self.cleaned_data["order"],
        )

    def get_params(self) -> dict:
        return {param: self.cleaned_data[param] for param in self.f_params}


class FullNameFieldForm(BaseFieldForm):
    type = "name"


class RandomIntFieldForm(BaseFieldForm):
    type = "random_int"
    label = "Random integer"

    min = forms.IntegerField(label="Min", min_value=-9999999, max_value=9999999, required=True)
    max = forms.IntegerField(label="Max", min_value=-9999999, max_value=9999999, required=True)

    def clean(self):
        cleaned_data = super().clean()
        min_ = cleaned_data.get("min")  # type: ignore
        max_ = cleaned_data.get("max")  # type: ignore
        if min_ > max_:  # type: ignore
            raise forms.ValidationError("Min must be less than max")

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


class SentencesFieldForm(BaseFieldForm):
    type = "sentences_variable_str"
    label = "Sentences"

    nb_min = forms.IntegerField(min_value=1, label="Min sentences")
    nb_max = forms.IntegerField(min_value=1, label="Min sentences")

    # ext_word_list = forms.CharField(
    #     label='Custom words (comma separated)',
    #     required=False,
    #     validators=[lambda str: [word.strip() for word in str.split(',')]]
    # )

    def clean(self):
        cleaned_data = super().clean()
        min_ = cleaned_data.get("nb_min")  # type: ignore
        max_ = cleaned_data.get("nb_max")  # type: ignore
        if min_ > max_:  # type: ignore
            raise forms.ValidationError("Min must be less than max")

        return cleaned_data


FIELD_FORMS = {field_form.type: field_form for field_form in BaseFieldForm.__subclasses__()}

# a temporal hack to init (call __new__) labels and stuff. Probably fixable by metaclasses.
[form() for form in FIELD_FORMS.values()]


def get_form_for_field(field: Field):
    return FIELD_FORMS[field.f_type](
        data={"name": field.name, "order": field.order, **field.f_params}
    )
