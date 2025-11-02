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
    path('toggle-active/<int:flight_id>/', views.toggle_flight_active, name='toggle_flight_active'),
    path('edit/<int:flight_id>/', views.edit_flight, name='edit_flight'),
    path('delete/<int:flight_id>/', views.delete_flight, name='delete_flight'),
    path('airplanes/', views.airplane_list, name='airplane_list'),
    path('airplanes/<int:airplane_id>/', views.airplane_detail, name='airplane_detail'),
    path('airplanes/<int:airplane_id>/edit/', views.edit_airplane, name='edit_airplane'),
    path('airplanes/<int:airplane_id>/delete/', views.delete_airplane, name='delete_airplane'),
    path('airplanes/<int:airplane_id>/toggle-active/', views.toggle_airplane_active, name='toggle_airplane_active'),
]
