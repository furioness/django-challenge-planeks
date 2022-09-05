from django.shortcuts import get_object_or_404

from rest_framework.decorators import action
from rest_framework.viewsets import (
    ModelViewSet,
    ReadOnlyModelViewSet,
)
from rest_framework.request import Request
from rest_framework.response import Response
from rest_framework import status
from rest_framework_extensions.mixins import NestedViewSetMixin


from ..models import Dataset, Schema
from .serializers import (
    SchemaSerializer,
    DatasetSerializer,
)


class SchemaViewSet(ModelViewSet):
    serializer_class = SchemaSerializer

    def get_queryset(self):
        return Schema.objects.filter(user=self.request.user)

    def perform_create(self, serializer):
        serializer.save(user=self.request.user)


class DatasetViewSet(NestedViewSetMixin, ReadOnlyModelViewSet):
    serializer_class = DatasetSerializer
    queryset = Dataset.objects.all()

    @action(methods=["post"], detail=False)
    def generate(self, request: Request, parent_lookup_schema: int):
        num_rows = request.data["num_rows"]
        schema = get_object_or_404(Schema, pk=parent_lookup_schema)
        dataset = schema.run_generate_task(num_rows)

        message = {"status": "Enqueued", "dataset": {"id": dataset.id}}
        return Response(data=message, status=status.HTTP_202_ACCEPTED)
