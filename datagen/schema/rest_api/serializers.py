from rest_framework import serializers

from ..models import Schema, BaseColumn


class ColumnSerializer(serializers.Serializer):
    type = serializers.CharField(max_length=255)
    params = serializers.DictField()

    def to_representation(self, instance):
        column_model = type(instance)
        class ConcreteColumnSerializer(serializers.ModelSerializer):
            class Meta:
                model = column_model
        repr = {"type": column_model.type,
                "params": ConcreteColumnSerializer(instance=instance).to_representation()}
        return repr

    def to_internal_value(self, data):
        try:
            column_model = BaseColumn.get_column_by_type(data["type"])
        except ValueError:
            raise serializers.ValidationError({"type": f"Column type '{data['type']}' doesn't exist"})

        try:
             column_instance = column_model(**data["params"])
        except Exception as exc:
            print(exc, type(exc))
            raise serializers.ValidationError({"params": f"Incorrect column params"})

        return column_instance


class SchemaSerializer(serializers.Serializer):
    name = serializers.CharField(max_length=255)
    column_separator = serializers.CharField(max_length=1, default=",")
    quotechar = serializers.CharField(max_length=1, default='"')
    columns = serializers.ListField(child=ColumnSerializer())

    def create(self, validated_data):
        schema = Schema(
            **validated_data, user=self.context.request.user
        )

        for column in validated_data["columns"]:
            column.schema = schema
            column.save()

        return schema


# {
#     "type": "rand_integer",
#     "params": {
#         "name": "Age",
#         "order": 1,
#         "min": 1,
#         "max": 5}
# }
