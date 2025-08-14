"""
repositories para la app de reservations
"""
from django.db.models import QuerySet
from typing import Optional
from apps.reservations.models import Reservation, Ticket


class ReservationRepository:
    """repository para manejar operaciones de reservation"""
    
    @staticmethod
    def get_all() -> QuerySet[Reservation]:
        """trae todas las reservations"""
        # select_related junta datos de vuelo, passenger y seat en la misma query para optimizar
        return Reservation.objects.select_related('flight', 'passenger', 'seat').all()
    
    @staticmethod
    def get_by_id(reservation_id: int) -> Optional[Reservation]:
        """busca una reservation por id"""
        try:
            # mismo que arriba, pero filtrando por id
            return Reservation.objects.select_related('flight', 'passenger', 'seat').get(id=reservation_id)
        except Reservation.DoesNotExist:
            # si no encuentra devuelve None en vez de romper
            return None
    
    @staticmethod
    def get_by_code(code: str) -> Optional[Reservation]:
        """busca una reservation por codigo"""
        try:
            # aca asume que el campo en la db se llama reservation_code
            return Reservation.objects.select_related('flight', 'passenger', 'seat').get(reservation_code=code)
        except Reservation.DoesNotExist:
            return None
    
    @staticmethod
    def get_by_passenger(passenger_id: int) -> QuerySet[Reservation]:
        """trae todas las reservations de un passenger"""
        # select_related aca trae datos de flight y seat junto con reservation
        return Reservation.objects.filter(passenger_id=passenger_id).select_related('flight', 'seat')
    
    @staticmethod
    def get_by_flight(flight_id: int) -> QuerySet[Reservation]:
        """trae todas las reservations de un flight"""
        return Reservation.objects.filter(flight_id=flight_id).select_related('passenger', 'seat')
    
    @staticmethod
    def create(data: dict) -> Reservation:
        """crea una reservation nueva"""
        # **data mete cada clave del dict como argumento
        return Reservation.objects.create(**data)
    
    @staticmethod
    def update_status(reservation_id: int, new_status: str) -> bool:
        """actualiza el status de una reservation"""
        try:
            # busca la reservation
            reservation = Reservation.objects.get(id=reservation_id)
            # le cambia el status
            reservation.status = new_status
            # guarda los cambios
            reservation.save()
            return True
        except Reservation.DoesNotExist:
            return False


class TicketRepository:
    """repository para manejar operaciones de ticket"""
    
    @staticmethod
    def get_by_reservation(reservation_id: int) -> Optional[Ticket]:
        """busca un ticket segun la reservation"""
        try:
            # select_related aca trae la reservation junto con el ticket
            return Ticket.objects.select_related('reservation').get(reservation_id=reservation_id)
        except Ticket.DoesNotExist:
            return None
    
    @staticmethod
    def get_by_code(barcode: str) -> Optional[Ticket]:
        """busca un ticket por su codigo de barras"""
        try:
            return Ticket.objects.select_related('reservation').get(barcode=barcode)
        except Ticket.DoesNotExist:
            return None
    
    @staticmethod
    def create(data: dict) -> Ticket:
        """crea un ticket nuevo"""
        return Ticket.objects.create(**data)
