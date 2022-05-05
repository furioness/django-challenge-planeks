from django.shortcuts import render
from django.contrib.auth.decorators import login_required


@login_required
def list_schemas(request):
    schemas = request.user.schemas.all()
    return render(request, 'schema/list.html', {'schemas': schemas})