from django.views.generic import CreateView, UpdateView, DeleteView, ListView
from django.contrib.auth.mixins import LoginRequiredMixin
from django.urls import reverse_lazy
from django.shortcuts import get_object_or_404, render

from .forms import GenerateForm, SchemaForm, FieldSelectForm
from .models import Schema



class BaseSchemaView(LoginRequiredMixin):
    def get_queryset(self):
        return self.request.user.schemas.all()
    
    
class CreateSchemaView(BaseSchemaView, CreateView):
    template_name = 'schema/edit.html'
    form_class = SchemaForm
    extra_context = {"fieldSelectForm": FieldSelectForm()}
    success_url = reverse_lazy('schema:list')
    
    def form_valid(self, form):
        form.instance.user = self.request.user
        return super().form_valid(form)
    
    
class UpdateSchemaView(BaseSchemaView, UpdateView):
    template_name = 'schema/edit.html'
    form_class = SchemaForm
    extra_context = {"fieldSelectForm": FieldSelectForm()}
    success_url = reverse_lazy('schema:list')
    
    
class DeleteSchemaView(BaseSchemaView, DeleteView):
    template_name = 'schema/delete.html'
    success_url = reverse_lazy('schema:list')
     
     
class ListSchemasView(BaseSchemaView, ListView):
    template_name = 'schema/list.html'
    context_object_name = 'schemas'


def list_data(request, schema_id):
    schema = get_object_or_404(Schema, id=schema_id)
    gen_form = GenerateForm()
    return render(request, 'schema/list_generated.html',
            {
                'schema_name': schema.name,
                'generated_data': schema.generated_data.all(),
                'gen_form': gen_form
            })


def generate(request, schema_id):

    schema = get_object_or_404(Schema, id=schema_id)
    
    schema.generate()
