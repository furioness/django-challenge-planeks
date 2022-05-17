# Generated by Django 4.0.4 on 2022-05-17 12:22

from django.conf import settings
import django.core.files.storage
from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    replaces = [
        ("schema", "0001_initial"),
        ("schema", "0002_schema_column_separator_schema_quotechar"),
        ("schema", "0003_rename_fields_schema_fields_json"),
        ("schema", "0004_rename_fields_json_schema_fields"),
        ("schema", "0005_alter_generateddata_schema"),
        ("schema", "0006_generateddata_generation_complete"),
        ("schema", "0007_alter_generateddata_schema"),
        ("schema", "0008_remove_generateddata_slug_generateddata_file"),
        ("schema", "0009_remove_generateddata_generation_complete"),
        ("schema", "0010_generateddata_created"),
        ("schema", "0011_alter_generateddata_created"),
        ("schema", "0012_rename_num_records_generateddata_num_rows_and_more"),
    ]

    initial = True

    dependencies = [migrations.swappable_dependency(settings.AUTH_USER_MODEL)]

    operations = [
        migrations.CreateModel(
            name="Schema",
            fields=[
                (
                    "id",
                    models.BigAutoField(
                        auto_created=True, primary_key=True, serialize=False, verbose_name="ID"
                    ),
                ),
                ("name", models.CharField(max_length=255)),
                ("fields", models.JSONField()),
                (
                    "user",
                    models.ForeignKey(
                        on_delete=django.db.models.deletion.CASCADE,
                        related_name="schemas",
                        to=settings.AUTH_USER_MODEL,
                    ),
                ),
                ("column_separator", models.CharField(default=",", max_length=1)),
                ("quotechar", models.CharField(default='"', max_length=1)),
            ],
        ),
        migrations.CreateModel(
            name="GeneratedData",
            fields=[
                (
                    "id",
                    models.BigAutoField(
                        auto_created=True, primary_key=True, serialize=False, verbose_name="ID"
                    ),
                ),
                ("num_rows", models.IntegerField()),
                (
                    "schema",
                    models.ForeignKey(
                        on_delete=django.db.models.deletion.CASCADE,
                        related_name="generated_data",
                        to="schema.schema",
                    ),
                ),
                (
                    "file",
                    models.FileField(
                        null=True,
                        storage=django.core.files.storage.FileSystemStorage(),
                        upload_to="",
                    ),
                ),
                ("created", models.DateTimeField(auto_now_add=True)),
            ],
        ),
    ]
