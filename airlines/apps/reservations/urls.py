"""
URLs para la app de reservas
"""
from django.urls import path
from . import views

app_name = 'reservations'

urlpatterns = [
    # vista principal para crear una nueva reserva
    path('new/<int:flight_id>/', views.new_reservation, name='new'),
    
    # si querés mantener la URL vacía para redirigir a una lista o nueva reserva,
    # la podemos dejar apuntando a new_reservation también
    path('', views.new_reservation, name='my_reservations'),
]
