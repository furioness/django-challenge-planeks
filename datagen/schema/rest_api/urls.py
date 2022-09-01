from rest_framework_extensions.routers import ExtendedDefaultRouter

from . import views


router = ExtendedDefaultRouter()

schemas = router.register(r"schemas", views.SchemaViewSet, basename="schemas")
schemas.register(
    r"datasets",
    views.DatasetViewSet,
    basename="datasets",
    parents_query_lookups=["schema"],
)

# The API URLs are now determined automatically by the router.
urlpatterns = router.urls
