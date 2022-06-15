from django.contrib import admin

from .models import Dataset, Schema, NameColumn, RandomIntColumn


admin.site.register(Dataset)

admin.site.register(NameColumn)
admin.site.register(RandomIntColumn)


class NameColumnInline(admin.TabularInline):
    model = NameColumn
    list_display = ("name",)


class SchemaAdmin(admin.ModelAdmin):
    inlines = [NameColumnInline]


admin.site.register(Schema, SchemaAdmin)
