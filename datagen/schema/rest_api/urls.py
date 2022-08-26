from django.urls import path, include
from rest_framework.routers import DefaultRouter
from rest_framework_extensions.routers import ExtendedDefaultRouter

from . import views


router = ExtendedDefaultRouter()
router.register(r"schemas", views.SchemaViewSet, basename="schemas").register(
    r"datasets",
    views.DatasetViewSet,
    basename="datasets",
    parents_query_lookups=["schema"],
)

# The API URLs are now determined automatically by the router.
urlpatterns = router.urls
