"""
ViewSets para la API REST.
"""
from .flight_views import FlightViewSet, AirplaneViewSet, SeatViewSet
from .passenger_views import PassengerViewSet
from .reservation_views import ReservationViewSet, TicketViewSet
from .report_views import ReportViewSet

__all__ = [
    'FlightViewSet',
    'AirplaneViewSet',
    'SeatViewSet',
    'PassengerViewSet',
    'ReservationViewSet',
    'TicketViewSet',
    'ReportViewSet',
]
