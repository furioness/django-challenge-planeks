from django.urls import path

from . import views

app_name = 'schema'


urlpatterns = [
    path('', views.list_schemas, name='list'),
    path('create/', views.create_schema, name='create'),
    path('edit/<int:pk>/', views.edit_schema, name='edit'),
    path('<int:pk>/', views.show_data, name='showdata'),
    path('delete/<int:pk>/', views.delete_data, name='delete'),
]