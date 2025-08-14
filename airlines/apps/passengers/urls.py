from django.urls import path
from . import views

app_name = 'pasajeros'

urlpatterns = [
    path('registro/', views.registro_pasajero, name='registro'),
    path('perfil/', views.perfil_pasajero, name='perfil'),
    path('editar/', views.editar_pasajero, name='editar'),
]