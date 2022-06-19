from django.contrib import admin

from .models import BaseColumn, Dataset, Schema


admin.site.register(
    Dataset, list_display=("id", "schema", "num_rows", "created", "file")
)


def column_inline_factory(model):
    return type(
        "whatever", (admin.TabularInline,), {"model": model, "extra": 0}
    )


class SchemaAdmin(admin.ModelAdmin):
    list_display = ("id", "name", "modified", "user")
    inlines = [
        column_inline_factory(column) for column in BaseColumn.__subclasses__()
    ]


admin.site.register(Schema, SchemaAdmin)
