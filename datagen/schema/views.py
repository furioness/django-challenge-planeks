from typing import Any, Dict

from django import forms
from django.shortcuts import render, redirect
from django.contrib.auth.mixins import LoginRequiredMixin
from django.shortcuts import get_object_or_404
from django.urls import reverse, reverse_lazy
from django.views.generic import (
    CreateView,
    DeleteView,
    FormView,
    ListView,
    UpdateView,
)

from .forms import GenerateForm, FieldSelectForm
from .models import Schema, BaseColumn


class BaseSchemaView(LoginRequiredMixin):
    def get_queryset(self):
        return self.request.user.schemas.all()  # type: ignore


# class CreateSchemaView(BaseSchemaView, CreateView):
#     template_name = "schema/edit.html"
#     form_class = SchemaForm
#     extra_context = {"fieldSelectForm": FieldSelectForm()}
#     success_url = reverse_lazy("schema:list")
#
#     def form_valid(self, form):
#         form.instance.user = self.request.user
#         return super().form_valid(form)


def create_schema_view(request):
    if request.method == "POST":
        schema_form = forms.modelform_factory(
            Schema, fields=("name", "column_separator", "quotechar")
        )(request.POST, prefix=Schema.__name__)
        column_formsets = [
            forms.modelformset_factory(
                Column,
                exclude=(
                    "id",
                    "schema",
                ),
            )(request.POST, prefix=Column.__name__)
            for Column in BaseColumn.__subclasses__()
        ]
        schema_valid = schema_form.is_valid()
        formsets_validity = [formset.is_valid() for formset in column_formsets]
        if schema_valid and all(formsets_validity):
            schema_form.instance.user = request.user
            schema_form.save()
            for column_formset in column_formsets:
                for column_form in column_formset:
                    column_form.instance.schema = schema_form.instance
                column_formset.save()
            return redirect(reverse("schema:list"))
    else:
        schema_form = forms.modelform_factory(
            Schema, fields=("name", "column_separator", "quotechar")
        )(prefix=Schema.__name__)
        column_formsets = [
            forms.modelformset_factory(
                Column,
                exclude=(
                    "id",
                    "schema",
                ),
            )(prefix=Column.__name__, queryset=Column.objects.none())
            for Column in BaseColumn.__subclasses__()
        ]
    return render(
        request,
        "schema/edit.html",
        {
            "schema_form": schema_form,
            "column_formsets": column_formsets,
            "field_select_form": FieldSelectForm(),
            "column_form_templates": [
                (
                    Column.__name__,
                    forms.modelform_factory(Column, exclude=("id", "schema"))(
                        prefix=Column.__name__ + "-!"
                    ),
                )
                for Column in BaseColumn.__subclasses__()
            ],
        },
    )


def edit_schema_view(request, pk):
    schema = get_object_or_404(Schema, pk=pk, user=request.user)
    if request.method == "POST":
        schema_form = forms.modelform_factory(
            Schema, fields=("name", "column_separator", "quotechar")
        )(request.POST, instance=schema, prefix=Schema.__name__)
        column_formsets = [
            forms.modelformset_factory(
                col_model,
                exclude=(
                    "id",
                    "schema",
                ),
                extra=0
            )(request.POST, queryset=columns, prefix=col_model.__name__)
            for col_model, columns in schema.columns_grouped_by_type
        ]
        schema_valid = schema_form.is_valid()
        formsets_validity = [formset.is_valid() for formset in column_formsets]
        if schema_valid and all(formsets_validity):
            schema_form.instance.user = request.user
            schema_form.save()
            for column_formset in column_formsets:
                for column_form in column_formset:
                    column_form.instance.schema = schema_form.instance
                column_formset.save()
            return redirect(reverse("schema:list"))
    else:
        schema_form = forms.modelform_factory(
            Schema, fields=("name", "column_separator", "quotechar")
        )(instance=schema, prefix=Schema.__name__)
        column_formsets = [
            forms.modelformset_factory(
                col_model,
                exclude=(
                    "id",
                    "schema",
                ),
                extra=0
            )(queryset=columns, prefix=col_model.__name__)
            for col_model, columns in schema.columns_grouped_by_type
        ]
    return render(
        request,
        "schema/edit.html",
        {
            "schema_form": schema_form,
            "column_formsets": column_formsets,
            "field_select_form": FieldSelectForm(),
            "column_form_templates": [
                (
                    Column.__name__,
                    forms.modelform_factory(Column, exclude=("id", "schema"))(
                        prefix=Column.__name__ + "-!"
                    ),
                )
                for Column in BaseColumn.__subclasses__()
            ],
        },
    )


# class UpdateSchemaView(BaseSchemaView, UpdateView):
#     template_name = "schema/edit.html"
#     form_class = SchemaForm
#     extra_context = {"fieldSelectForm": FieldSelectForm()}
#     success_url = reverse_lazy("schema:list")


class DeleteSchemaView(BaseSchemaView, DeleteView):
    template_name = "schema/delete.html"
    success_url = reverse_lazy("schema:list")


class ListSchemasView(BaseSchemaView, ListView):
    template_name = "schema/list.html"
    context_object_name = "schemas"


class SchemaDataSetsView(BaseSchemaView, FormView):
    template_name = "data/list.html"
    form_class = GenerateForm

    def get_object(self):
        return get_object_or_404(self.get_queryset(), pk=self.kwargs["pk"])

    def get_context_data(self, **kwargs: Any) -> Dict[str, Any]:
        context = super().get_context_data(**kwargs)
        context["schema"] = self.get_object()
        return context

    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        kwargs["request"] = self.request
        return kwargs

    def form_valid(self, form):
        self.get_object().run_generate_task(form.cleaned_data["num_rows"])  # type: ignore
        return super().form_valid(form)

    def get_success_url(self):
        return reverse("schema:datasets", args=(self.get_object().pk,))  # type: ignore
