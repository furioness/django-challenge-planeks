from rest_framework import authentication
from rest_framework import mixins
from rest_framework.viewsets import GenericViewSet, ModelViewSet

from ..models import Schema
from .serializers import SchemaCreateRetrieveSerializer, SchemaUpdateSerializer


class CommonSchemaViewMixin:
    authentication_classes = (
        authentication.SessionAuthentication,
        authentication.BasicAuthentication,
    )

    def get_queryset(self):
        return Schema.objects.filter(user=self.request.user)


class SchemaViewSet(CommonSchemaViewMixin, ModelViewSet):
    def get_serializer_class(self):
        if self.request.method in ("PUT", "PATCH"):
            return SchemaUpdateSerializer

        return SchemaCreateRetrieveSerializer
