from django.core.exceptions import ValidationError
from rest_framework import serializers

from ..models import Schema, BaseColumn


class ColumnSerializer(serializers.Serializer):
    type = serializers.CharField(max_length=255)
    params = serializers.DictField()

    def to_representation(self, instance) -> BaseColumn:
        column_model = type(instance)

        class ConcreteColumnSerializer(serializers.ModelSerializer):
            class Meta:
                model = column_model
                exclude = ("schema",)

        repr = {
            "type": column_model.type,
            "params": ConcreteColumnSerializer(
                instance=instance
            ).to_representation(instance),
        }
        return repr

    def to_internal_value(self, data):
        try:
            column_model = BaseColumn.get_column_by_type(data["type"])
        except ValueError:
            raise serializers.ValidationError(
                {"type": f"Column type '{data['type']}' doesn't exist"}
            )

        try:
            column_instance = column_model(**data["params"])
        except Exception as exc:
            raise serializers.ValidationError(
                {"params": f"Incorrect column params"}
            ) from exc

        try:
            column_instance.full_clean(exclude=["schema"])
        except ValidationError as exc:
            raise serializers.ValidationError(exc.message_dict)

        return column_instance


class SchemaCreateRetrieveSerializer(serializers.Serializer):
    id = serializers.IntegerField()
    name = serializers.CharField(max_length=255)
    column_separator = serializers.CharField(max_length=1, default=",")
    quotechar = serializers.CharField(max_length=1, default='"')
    columns = serializers.ListField(child=ColumnSerializer())

    def create(self, validated_data) -> Schema:
        columns = validated_data.pop("columns")
        schema = Schema.objects.create(
            **validated_data, user=self.context["request"].user
        )

        for column in columns:
            column.schema = schema
            column.save()

        return schema


class SchemaUpdateSerializer(serializers.ModelSerializer):
    class Meta:
        model = Schema
        exclude = ("user", "modified")
