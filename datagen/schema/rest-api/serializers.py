from functools import cache

from rest_framework import serializers

from ..models import Schema, BaseColumn


class SchemaEditSerializer(serializers.Serializer):
    name = serializers.CharField(max_length=255)
    column_separator = serializers.CharField(max_length=1, default=",")
    quotechar = serializers.CharField(max_length=1, default='"')
    columns = serializers.JSONField()

    def create(self, validated_data):
        columns = validated_data.pop["datasets"]
        schema = Schema.objects.create(
            **validated_data, user=self.context.request.user
        )

        for column in columns:
            column_model = BaseColumn.get_column_by_type(column["type"])
            column_serializer = self.get_column_create_serializer(column_model)
            
            column_model.objects.create(
                schema=schema, **column_serializer(column["params"])
            )

        return schema

    @staticmethod
    @cache
    def get_column_create_serializer(column_model):
        class ColumnMeta:
            model = column_model
            exclude = ["id", "schema"]

        return type(f'{column_model.__name__}CreateSerializer', (serializers.ModelSerializer), {"Meta": ColumnMeta})


# {
#     "type": "rand_integer",
#     "params": {
#         "name": "Age",
#         "order": 1,
#         "min": 1,
#         "max": 5}
# }
