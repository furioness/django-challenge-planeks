from django.urls import path, include

from . import views
from .rest_api import urls as api_urls

app_name = "schema"


urlpatterns = [
    path("", views.ListSchemasView.as_view(), name="list"),
    path("create/", views.CreateSchemaView.as_view(), name="create"),
    path("<int:pk>/edit/", views.EditSchemaView.as_view(), name="edit"),
    path("<int:pk>/delete/", views.DeleteSchemaView.as_view(), name="delete"),
    path("<int:pk>/", views.SchemaDataSetsView.as_view(), name="datasets"),
    path("api/", include(api_urls.urlpatterns)),
]
