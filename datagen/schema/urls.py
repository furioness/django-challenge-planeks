from django.urls import path

from . import views

app_name = 'schema'


urlpatterns = [
    path('', views.ListSchemasView.as_view(), name='list'),
    path('create/', views.CreateSchemaView.as_view(), name='create'),
    path('edit/<int:pk>/', views.UpdateSchemaView.as_view(), name='update'),
    # path('<int:pk>/', views.show_data, name='showdata'),
    path('delete/<int:pk>/', views.DeleteSchemaView.as_view(), name='delete'),
    path('data/<int:schema_id>/', views.list_data, name='list-data'),
    path('data/<int:schema_id>/generate/', views.generate, name='generate'),
    
]