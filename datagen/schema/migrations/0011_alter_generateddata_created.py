# Generated by Django 4.0.4 on 2022-05-09 11:19

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [("schema", "0010_generateddata_created")]

    operations = [
        migrations.AlterField(
            model_name="generateddata",
            name="created",
            field=models.DateTimeField(auto_now_add=True),
        )
    ]
