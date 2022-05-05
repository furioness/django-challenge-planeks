from django.contrib import admin

from .models import GeneratedData, Schema


admin.site.register(GeneratedData)
admin.site.register(Schema)
