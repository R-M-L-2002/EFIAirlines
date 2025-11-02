from django.urls import path
from . import views

app_name = 'reservations'

urlpatterns = [
    path('new/<int:flight_id>/', views.new_reservation, name='new'),
    path('confirm/<str:reservation_code>/', views.confirm_and_pay_reservation, name='confirm'), 
    path('payment/<str:reservation_code>/', views.confirm_and_pay_reservation, name='payment'),
    path('payment-success/<str:reservation_code>/', views.payment_success, name='payment_success'),
    path('download-ticket/<str:reservation_code>/', views.download_ticket_pdf, name='download_ticket'),
    path('cancel/<str:reservation_code>/', views.cancel_reservation, name='cancel'),
    path('mine/', views.my_reservations, name='my_reservations'),
    path('<str:reservation_code>/', views.reservation_detail, name='detail'),
]
