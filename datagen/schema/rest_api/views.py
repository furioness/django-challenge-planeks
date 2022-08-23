from rest_framework import authentication
from rest_framework import mixins
from rest_framework.viewsets import GenericViewSet

from ..models import Schema
from .serializers import SchemaCreateSerializer, SchemaUpdateSerializer


class CommonSchemaViewMixin:
    authentication_classes = (
        authentication.SessionAuthentication,
        authentication.BasicAuthentication,
    )

    def get_queryset(self):
        return Schema.objects.filter(user=self.request.user)


class SchemaCreateListRetrieveDeleteViewSet(
    CommonSchemaViewMixin,
    mixins.CreateModelMixin,
    mixins.ListModelMixin,
    mixins.RetrieveModelMixin,
    mixins.DestroyModelMixin,
    GenericViewSet,
):
    serializer_class = (SchemaCreateSerializer,)


class SchemaUpdateView(
    CommonSchemaViewMixin, mixins.UpdateModelMixin, GenericViewSet
):
    serializer_class = (SchemaUpdateSerializer,)
