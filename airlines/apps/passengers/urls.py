"""
URLs para la app de pasajeros
"""
from django.urls import path
from . import views

app_name = 'passengers'

urlpatterns = [
    path('register/', views.register_passenger, name='register'),
    path('profile/', views.passenger_profile, name='profile'),
    path('profile/edit/', views.edit_passenger, name='edit'), 
]
