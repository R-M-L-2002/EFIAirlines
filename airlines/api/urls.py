"""
URLs para la API REST.
"""
from django.urls import path, include
from rest_framework.routers import DefaultRouter
from rest_framework.authtoken.views import obtain_auth_token

from drf_spectacular.views import (
    SpectacularAPIView,
    SpectacularSwaggerView,
    SpectacularRedocView,
)

from api.views import (
    FlightViewSet,
    AirplaneViewSet,
    SeatViewSet,
    PassengerViewSet,
    ReservationViewSet,
    TicketViewSet,
    ReportViewSet
)

# Router para registrar los ViewSets
router = DefaultRouter()
router.register(r'flights', FlightViewSet, basename='flight')
router.register(r'airplanes', AirplaneViewSet, basename='airplane')
router.register(r'seats', SeatViewSet, basename='seat')
router.register(r'passengers', PassengerViewSet, basename='passenger')
router.register(r'reservations', ReservationViewSet, basename='reservation')
router.register(r'tickets', TicketViewSet, basename='ticket')
router.register(r'reports', ReportViewSet, basename='report')

urlpatterns = [
    # Formato JSON (para Swagger)
    path('schema/', SpectacularAPIView.as_view(), name='schema'),

    # Swagger UI (documentación interactiva)
    path('swagger/', SpectacularSwaggerView.as_view(url_name='schema'), name='swagger-ui'),

    #Redoc UI (otra interfaz de documentación)
    path('redoc/', SpectacularRedocView.as_view(url_name='schema'), name='redoc'),

    # Autenticación con Token
    path('auth/token/', obtain_auth_token, name='api_token_auth'),

    # Endpoints de la API REST
    path('', include(router.urls)),
]
