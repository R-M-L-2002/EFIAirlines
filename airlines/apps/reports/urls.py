"""
URLs para la app de reportes
"""

from django.urls import path
from . import views

app_name = 'reports'

urlpatterns = [
    path('', views.reports_dashboard, name='dashboard'),
    path('flight-passengers/<int:flight_id>/', views.flight_passengers_report, name='flight_passengers'),
    path('income/', views.income_report, name='income'),
    path('export/', views.export_data, name='export'),
]