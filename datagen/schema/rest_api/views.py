from django.shortcuts import get_object_or_404

from rest_framework import authentication
from rest_framework import mixins
from rest_framework.decorators import action
from rest_framework.viewsets import (
    GenericViewSet,
    ModelViewSet,
    ReadOnlyModelViewSet,
)
from rest_framework.request import Request
from rest_framework.response import Response
from rest_framework import status
from rest_framework_extensions.mixins import NestedViewSetMixin


from ..models import Dataset, Schema
from .serializers import (
    SchemaCreateRetrieveSerializer,
    SchemaUpdateSerializer,
    DatasetSerializer,
)


class SchemaViewSet(ModelViewSet):
    def get_queryset(self):
        return Schema.objects.filter(user=self.request.user)

    def get_serializer_class(self):
        if self.request.method in ("PUT", "PATCH"):
            return SchemaUpdateSerializer

        return SchemaCreateRetrieveSerializer


class DatasetViewSet(NestedViewSetMixin, ReadOnlyModelViewSet):
    serializer_class = DatasetSerializer
    queryset = Dataset.objects.all()

    @action(methods=["post"], detail=False)
    def generate(self, request: Request, parent_lookup_schema: int):
        num_rows = request.data["num_rows"]
        schema = get_object_or_404(Schema, pk=parent_lookup_schema)
        schema.run_generate_task(num_rows)

        return Response(status=status.HTTP_202_ACCEPTED)
