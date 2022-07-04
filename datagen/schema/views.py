from typing import Any, Dict

from django.contrib.auth.mixins import LoginRequiredMixin
from django.db import transaction
from django.db.models import QuerySet
from django.forms import Form
from django.http.response import HttpResponse
from django.shortcuts import get_object_or_404
from django.urls import reverse, reverse_lazy
from django.views.generic import (
    CreateView,
    DeleteView,
    FormView,
    ListView,
    UpdateView,
)

from .forms import FieldSelectForm, GenerateForm, SchemaForm
from .models import Schema


class OwnSchemaMixin(LoginRequiredMixin):
    def get_queryset(self) -> QuerySet[Schema]:
        return self.request.user.schemas.all()  # type: ignore[no-any-return, attr-defined]


class AtomicFormSavingMixin:
    @transaction.atomic
    def form_valid(self, form: Form) -> HttpResponse:
        return super().form_valid(form)  # type: ignore[no-any-return, misc]


class CreateSchemaView(OwnSchemaMixin, AtomicFormSavingMixin, CreateView):  # type: ignore[misc]
    template_name = "schema/edit.html"
    form_class = SchemaForm
    prefix = "Schema"
    extra_context = {"field_select_form": FieldSelectForm()}
    success_url = reverse_lazy("schema:list")

    def get_form_kwargs(self) -> Dict[str, Any]:
        kwargs = super().get_form_kwargs()
        kwargs["user"] = self.request.user
        return kwargs


class EditSchemaView(OwnSchemaMixin, AtomicFormSavingMixin, UpdateView):  # type: ignore[misc]
    template_name = "schema/edit.html"
    form_class = SchemaForm
    prefix = "Schema"
    extra_context = {"field_select_form": FieldSelectForm()}
    success_url = reverse_lazy("schema:list")

    def get_form_kwargs(self) -> Dict[str, Any]:
        kwargs = super().get_form_kwargs()
        kwargs["user"] = self.request.user
        return kwargs


class DeleteSchemaView(OwnSchemaMixin, DeleteView):
    template_name = "schema/delete.html"
    success_url = reverse_lazy("schema:list")


class ListSchemasView(OwnSchemaMixin, ListView):
    template_name = "schema/list.html"
    context_object_name = "schemas"


class SchemaDataSetsView(OwnSchemaMixin, FormView):
    template_name = "data/list.html"
    form_class = GenerateForm

    def get_object(self) -> Schema:
        return get_object_or_404(self.get_queryset(), pk=self.kwargs["pk"])

    def get_context_data(self, **kwargs: Any) -> Dict[str, Any]:
        context = super().get_context_data(**kwargs)
        context["schema"] = self.get_object()
        return context

    def get_form_kwargs(self) -> Dict[str, Any]:
        kwargs = super().get_form_kwargs()
        kwargs["request"] = self.request
        return kwargs

    def form_valid(self, form: GenerateForm) -> HttpResponse:
        self.get_object().run_generate_task(form.cleaned_data["num_rows"])
        return super().form_valid(form)

    def get_success_url(self) -> str:
        return reverse("schema:datasets", args=(self.get_object().pk,))
