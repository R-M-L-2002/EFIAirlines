"""
URLs para la app de vuelos
"""
from django.urls import path
from . import views

app_name = 'flights'

urlpatterns = [
    path('', views.flight_list, name='list'),
    path('<int:flight_id>/', views.flight_detail, name='detail'),
    path('create-airplane/', views.create_airplane, name='create_airplane'),
    path('create-flight/', views.create_flight, name='create_flight'),
]
