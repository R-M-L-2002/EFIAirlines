"""
Serializers para transformar modelos en JSON.
"""
from .flight_serializers import (
    FlightSerializer,
    FlightListSerializer,
    FlightDetailSerializer,
    AirplaneSerializer,
    SeatSerializer
)
from .passenger_serializers import (
    PassengerSerializer,
    PassengerCreateSerializer,
    PassengerDetailSerializer
)
from .reservation_serializers import (
    ReservationSerializer,
    ReservationCreateSerializer,
    ReservationDetailSerializer,
    TicketSerializer
)

__all__ = [
    'FlightSerializer',
    'FlightListSerializer',
    'FlightDetailSerializer',
    'AirplaneSerializer',
    'SeatSerializer',
    'PassengerSerializer',
    'PassengerCreateSerializer',
    'PassengerDetailSerializer',
    'ReservationSerializer',
    'ReservationCreateSerializer',
    'ReservationDetailSerializer',
    'TicketSerializer',
]
