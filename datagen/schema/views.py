from django.shortcuts import render, redirect, get_object_or_404
from django.http import HttpRequest

from django.contrib.auth.decorators import login_required

from .forms import GenerateForm, SchemaForm, FieldSelectForm
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
        if schema_form.is_valid():
            Schema.objects.create(**schema_form.cleaned_data, user=request.user)
            return redirect('schema:list')
        
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

def list_data(request, schema_id):
    schema = get_object_or_404(Schema, id=schema_id)
    gen_form = GenerateForm()
    return render(request, 'schema/list_generated.html',
            {
                'schema_name': schema.name,
                'generated_data': schema.generated_data.all(),
                'gen_form': gen_form
            })

def delete_schema(request, schema_id):
    pass


def generate(request, schema_id):

    schema = get_object_or_404(Schema, id=schema_id)
    
    schema.generate()