from django.shortcuts import render, redirect, get_object_or_404
from django.http import HttpRequest

from django.contrib.auth.decorators import login_required

from .forms import SchemaForm, FieldSelectForm
from .utils.field_forms import FIELD_FORMS
from .models import Schema


@login_required
def list_schemas(request: HttpRequest):
    schemas = request.user.schemas.all()  # type: ignore
    return render(request, 'schema/list.html', {'schemas': schemas})


@login_required
def create_schema(request: HttpRequest):
    schema_form = SchemaForm()
    field_forms = []
    if request.method == 'POST':
        schema_form = SchemaForm(request.POST)
        is_schema_form_valid = schema_form.is_valid()

        schema = Schema(**schema_form.cleaned_data, user=request.user)
        field_forms = schema.get_field_forms()
        are_fields_valid = all(form.is_valid() for form in field_forms)
        if is_schema_form_valid and are_fields_valid:
            Schema.objects.create(**schema_form.cleaned_data, user=request.user)
            return redirect('schema:list')
        schema = Schema(**schema_form.cleaned_data, user=request.user)
        
    return render(request, 'schema/edit.html', {
        'schemaForm': schema_form,
        'fieldForms': field_forms,
        'fieldFormsTemplates': FIELD_FORMS,
        'fieldSelectForm': FieldSelectForm(),
        })
    
@login_required    
def edit_schema(request, schema_id):
    schema = get_object_or_404(Schema, id=schema_id)
    schema_form = SchemaForm({'name': schema.name,
                             'fields_json': schema.fields_json,
                             'column_separator': schema.column_separator,
                             'quotechar': schema.quotechar})
    
    return render(request, 'schema/edit.html', {
        'schemaForm': schema_form,
        'fieldForms': FIELD_FORMS,
        'fieldSelectForm': FieldSelectForm(),
        })

def show_data(request, schema_id):
    pass

def delete_schema(request, schema_id):
    pass
