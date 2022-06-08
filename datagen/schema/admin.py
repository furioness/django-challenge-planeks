from django.contrib import admin

from .models import Dataset, Schema


admin.site.register(Dataset)
admin.site.register(Schema)
