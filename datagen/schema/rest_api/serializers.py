from typing import List, Type
from django.core.exceptions import ValidationError
from rest_framework import serializers

from ..models import Dataset, NoColumnException, Schema, BaseColumn


class ColumnSerializer(serializers.Serializer):
    type = serializers.CharField(max_length=255)
    params = serializers.DictField()

    def to_representation(self, instance) -> BaseColumn:
        column_model = type(instance)
        ConcreteColumnSerializer = self._get_concrete_column_serializer(
            column_model
        )

        representation = {
            "type": column_model.type,
            "params": ConcreteColumnSerializer(
                instance=instance
            ).to_representation(instance),
        }
        return representation

    def to_internal_value(self, data):
        col_type = data["type"]
        try:
            col_model = BaseColumn.get_column_by_type(col_type)
        except NoColumnException as exc:
            raise serializers.ValidationError(exc)

        ConcreteColumnSerializer = self._get_concrete_column_serializer(
            col_model
        )
        column_serializer = ConcreteColumnSerializer(data=data["params"])
        if not column_serializer.is_valid():
            raise serializers.ValidationError(column_serializer.errors)

        column_instance = col_model(**column_serializer.validated_data)
        try:
            column_instance.full_clean(exclude=["schema"])
        except ValidationError as exc:
            raise serializers.ValidationError(exc.message_dict)

        return column_instance

    def _get_concrete_column_serializer(
        self, col_model
    ) -> Type[serializers.ModelSerializer]:
        class ConcreteColumnSerializer(serializers.ModelSerializer):
            class Meta:
                model = col_model
                exclude = ("schema", "id")
                extra_kwargs = {"order": {"required": True}}

        return ConcreteColumnSerializer


class SchemaSerializer(serializers.Serializer):
    id = serializers.IntegerField(read_only=True)
    name = serializers.CharField(max_length=255)
    column_separator = serializers.CharField(max_length=1, default=",")
    quotechar = serializers.CharField(max_length=1, default='"')
    columns = serializers.ListField(child=ColumnSerializer())

    def create(self, validated_data) -> Schema:
        columns: List[BaseColumn] = validated_data.pop("columns")
        # self.context["request"] is provided by GenericAPIView
        schema = Schema.objects.create(**validated_data)
        self._append_columns(schema, columns)

        return schema

    def update(self, instance, validated_data):
        columns = validated_data.pop("columns", None)
        if columns:
            self._append_columns(instance, columns, remove_previous=True)

        instance.__dict__.update(**validated_data)
        instance.save()
        return instance

    @staticmethod
    def _append_columns(schema, columns, remove_previous=False):
        if remove_previous:
            for column in schema.columns:
                column.delete()

        for column in columns:
            column.schema = schema
            column.save()

        return schema


class DatasetSerializer(serializers.ModelSerializer):
    class Meta:
        model = Dataset
        exclude = ("schema",)
