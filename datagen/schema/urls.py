from django.urls import path

from . import views

app_name = 'schema'


urlpatterns = [
    path('', views.list_schemas, name='list'),
    path('create/', views.create_schema, name='create'),
    path('edit/<int:schema_id>/', views.edit_schema, name='edit'),
    path('delete/<int:schema_id>/', views.delete_schema, name='delete'),
    path('data/<int:schema_id>/', views.list_data, name='list-data'),
    path('data/<int:schema_id>/generate/', views.generate, name='generate'),
    
]