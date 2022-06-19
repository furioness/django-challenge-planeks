from django.urls import path

from . import views

app_name = "schema"


urlpatterns = [
    path("", views.ListSchemasView.as_view(), name="list"),
    path("create/", views.CreateSchemaView.as_view(), name="create"),
    path("<int:pk>/edit/", views.EditSchemaView.as_view(), name="edit"),
    path("<int:pk>/delete/", views.DeleteSchemaView.as_view(), name="delete"),
    path("<int:pk>/", views.SchemaDataSetsView.as_view(), name="datasets"),
]
