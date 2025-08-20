from django.urls import path
from . import views

app_name = 'reservations'

urlpatterns = [
    path('new/<int:flight_id>/', views.new_reservation, name='new'),
    path('confirm/<str:reservation_code>/', views.confirm_reservation, name='confirm'),
    path('cancel/<str:reservation_code>/', views.cancel_reservation, name='cancel'),
    path('mine/', views.my_reservations, name='my_reservations'),  # ← aquí antes de detail
    path('<str:reservation_code>/', views.detail, name='detail'),
    
]
