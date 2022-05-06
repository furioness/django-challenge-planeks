from django.views.generic import CreateView, UpdateView, DeleteView, ListView
from django.contrib.auth.mixins import LoginRequiredMixin
from django.urls import reverse_lazy

from .forms import SchemaForm, FieldSelectForm



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
