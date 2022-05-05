from django.urls import path

from . import views

app_name = 'schema'


urlpatterns = [
    path('', views.list_schemas, name='list'),
]