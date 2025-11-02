"""
Repositorio para operaciones de datos de Reservation y Ticket.
"""
from typing import List, Optional
from django.db.models import Q, QuerySet
from django.utils import timezone
from datetime import datetime, timedelta
from apps.reservations.models import Reservation, Ticket
from apps.passengers.models import Passenger
from apps.flights.models import Flight


class ReservationRepository:
    """Repositorio para gestionar operaciones de reservas"""
    
    @staticmethod
    def get_by_id(reservation_id: int) -> Optional[Reservation]:
        """Obtiene una reserva por su ID"""
        try:
            return Reservation.objects.select_related(
                'flight', 'passenger', 'seat', 'flight__airplane'
            ).get(id=reservation_id)
        except Reservation.DoesNotExist:
            return None

    @staticmethod
    def get_by_code(reservation_code: str) -> Optional[Reservation]:
        """Obtiene una reserva por su código"""
        try:
            return Reservation.objects.select_related(
                'flight', 'passenger', 'seat', 'flight__airplane'
            ).get(reservation_code=reservation_code)
        except Reservation.DoesNotExist:
            return None

    @staticmethod
    def get_by_passenger(passenger: Passenger) -> QuerySet:
        """Obtiene todas las reservas de un pasajero (incluye canceladas y completadas)"""
        return Reservation.objects.filter(
            passenger=passenger
        ).select_related(
            'flight', 'seat', 'flight__airplane'
        ).order_by('-reservation_date')

    @staticmethod
    def get_by_flight(flight: Flight) -> QuerySet:
        """Obtiene todas las reservas de un vuelo"""
        return Reservation.objects.filter(
            flight=flight
        ).select_related('passenger', 'seat').order_by('seat__row', 'seat__column')

    @staticmethod
    def get_active_by_passenger(passenger: Passenger) -> QuerySet:
        """Obtiene reservas activas de un pasajero (excluye canceladas y completadas)"""
        return Reservation.objects.filter(
            passenger=passenger,
            status__in=[Reservation.STATUS_PENDING, Reservation.STATUS_CONFIRMED, Reservation.STATUS_PAID]
        ).select_related('flight', 'seat').order_by('flight__departure_date')

    @staticmethod
    def create(data: dict) -> Reservation:
        """Crea una nueva reserva"""
        return Reservation.objects.create(**data)

    @staticmethod
    def update(reservation: Reservation, data: dict) -> Reservation:
        """Actualiza una reserva existente"""
        for key, value in data.items():
            setattr(reservation, key, value)
        reservation.save()
        return reservation

    @staticmethod
    def delete(reservation: Reservation) -> None:
        """Elimina una reserva"""
        reservation.delete()

    @staticmethod
    def check_existing_reservation(flight: Flight, passenger: Passenger) -> Optional[Reservation]:
        """Verifica si existe una reserva activa para un vuelo y pasajero (excluye canceladas)"""
        return Reservation.objects.filter(
            flight=flight,
            passenger=passenger
        ).exclude(status=Reservation.STATUS_CANCELLED).first()


    @staticmethod
    def get_occupied_seats(flight: Flight) -> List[int]:
        """Obtiene IDs de asientos ocupados para un vuelo"""
        return list(
            Reservation.objects.filter(flight=flight)
            .filter(
                Q(status__in=[Reservation.STATUS_CONFIRMED, Reservation.STATUS_PAID, Reservation.STATUS_COMPLETED]) |
                Q(status=Reservation.STATUS_PENDING, expiration_date__gt=timezone.now())
            )
            .values_list('seat_id', flat=True)
        )

    @staticmethod
    def count_by_status(status: str, passenger: Optional[Passenger] = None) -> int:
        """Cuenta reservas por estado (opcionalmente filtradas por pasajero)"""
        query = Reservation.objects.filter(status=status)
        if passenger:
            query = query.filter(passenger=passenger)
        return query.count()

    @staticmethod
    def get_upcoming_by_passenger(passenger: Passenger, limit: int = 3) -> QuerySet:
        """Obtiene próximas reservas de un pasajero"""
        return Reservation.objects.filter(
            passenger=passenger,
            status__in=[Reservation.STATUS_CONFIRMED, Reservation.STATUS_PAID],
            flight__departure_date__gte=timezone.now()
        ).select_related('flight', 'seat').order_by('flight__departure_date')[:limit]

    @staticmethod
    def get_history_by_passenger(passenger: Passenger, limit: int = 5) -> QuerySet:
        """Obtiene historial de reservas de un pasajero (completadas o canceladas)"""
        return Reservation.objects.filter(
            passenger=passenger,
            status__in=[Reservation.STATUS_COMPLETED, Reservation.STATUS_CANCELLED]
        ).select_related('flight', 'seat').order_by('-reservation_date')[:limit]
    
    @staticmethod
    def get_by_date_range(start_date: datetime, end_date: datetime, status: list = None):
        """
        Obtiene reservas entre un rango de fechas y opcionalmente por estado.
        """
        query = Reservation.objects.filter(
            reservation_date__date__gte=start_date,
            reservation_date__date__lte=end_date
        )
        if status:
            query = query.filter(status__in=status)
        return query.select_related('passenger', 'seat', 'flight', 'flight__airplane')


class TicketRepository:
    """Repositorio para gestionar operaciones de tickets"""
    
    @staticmethod
    def get_by_id(ticket_id: int) -> Optional[Ticket]:
        """Obtiene un ticket por su ID"""
        try:
            return Ticket.objects.select_related('reservation').get(id=ticket_id)
        except Ticket.DoesNotExist:
            return None

    @staticmethod
    def get_by_barcode(barcode: str) -> Optional[Ticket]:
        """Obtiene un ticket por su código de barras"""
        try:
            return Ticket.objects.select_related('reservation').get(barcode=barcode)
        except Ticket.DoesNotExist:
            return None

    @staticmethod
    def get_by_reservation(reservation: Reservation) -> Optional[Ticket]:
        """Obtiene el ticket de una reserva"""
        try:
            return Ticket.objects.get(reservation=reservation)
        except Ticket.DoesNotExist:
            return None

    @staticmethod
    def create(data: dict) -> Ticket:
        """Crea un nuevo ticket"""
        return Ticket.objects.create(**data)

    @staticmethod
    def update(ticket: Ticket, data: dict) -> Ticket:
        """Actualiza un ticket existente"""
        for key, value in data.items():
            setattr(ticket, key, value)
        ticket.save()
        return ticket

    @staticmethod
    def delete(ticket: Ticket) -> None:
        """Elimina un ticket"""
        ticket.delete()

    @staticmethod
    def get_by_date_range(start_date, end_date) -> QuerySet:
        """
        Devuelve todas las reservas cuyo created_at esté entre start_date y end_date
        """
        return Reservation.objects.filter(
            created_at__gte=start_date,
            created_at__lte=end_date
        ).select_related('flight', 'seat', 'passenger', 'flight__airplane').order_by('created_at')
