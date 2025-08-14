"""
services para la app de reservations
"""
from typing import Optional, Dict
from django.db import transaction
from django.utils import timezone
from repositories.reservation import ReservationRepository, TicketRepository
from services.flight import SeatService, FlightService
from repositories.passenger import PassengerRepository
from apps.reservations.models import Reservation, Ticket
import uuid


class ReservationService:
    """service para la logica de negocio de Reservation"""
    
    @staticmethod
    def create_reservation(flight_id: int, passenger_id: int, seat_id: int) -> Optional[Reservation]:
        """crea una reservation completa con validaciones"""
        with transaction.atomic():  # para que todo pase o nada, si falla se revierte
            # chequear que el vuelo tenga asientos disponibles
            if not FlightService.check_flight_availability(flight_id):
                raise ValueError("el vuelo no tiene asientos disponibles")
            
            # chequear que el passenger exista
            passenger = PassengerRepository.get_by_id(passenger_id)
            if not passenger:
                raise ValueError("el passenger no existe")
            
            # reservar el asiento
            if not SeatService.reserve_seat(seat_id):
                raise ValueError("el asiento no esta disponible")
            
            # crear la reservation
            reservation_data = {
                'flight_id': flight_id,
                'passenger_id': passenger_id,
                'seat_id': seat_id,
                'reservation_code': ReservationService._generate_reservation_code(),
                'status': 'pending',
                'reservation_date': timezone.now()
            }
            
            reservation = ReservationRepository.create(reservation_data)
            
            # crear ticket automaticamente
            TicketService.create_ticket_for_reservation(reservation.id)
            
            return reservation
    
    @staticmethod
    def confirm_reservation(reservation_id: int) -> bool:
        """confirma una reservation y marca el asiento como ocupado"""
        with transaction.atomic():
            reservation = ReservationRepository.get_by_id(reservation_id)
            if not reservation or reservation.status != 'pending':
                return False
            
            # actualizar estado de reservation
            ReservationRepository.update_status(reservation_id, 'confirmed')
            
            # marcar asiento como ocupado
            SeatService.reserve_seat(reservation.seat.id)
            
            return True
    
    @staticmethod
    def cancel_reservation(reservation_id: int, reason: str = None) -> bool:
        """cancela una reservation y libera el asiento"""
        with transaction.atomic():
            reservation = ReservationRepository.get_by_id(reservation_id)
            if not reservation:
                return False
            
            # liberar asiento
            SeatService.release_seat(reservation.seat.id)
            
            # actualizar estado de reservation
            ReservationRepository.update_status(reservation_id, 'cancelled')
            
            return True
    
    @staticmethod
    def _generate_reservation_code() -> str:
        """genera un codigo unico para la reservation"""
        return f"RES-{uuid.uuid4().hex[:8].upper()}"


class TicketService:
    """service para la logica de negocio de Ticket"""
    
    @staticmethod
    def create_ticket_for_reservation(reservation_id: int) -> Optional[Ticket]:
        """crea un ticket electronico para una reservation"""
        reservation = ReservationRepository.get_by_id(reservation_id)
        if not reservation:
            return None
        
        ticket_data = {
            'reservation_id': reservation_id,
            'barcode': TicketService._generate_barcode(),
            'issue_date': timezone.now(),
            'status': 'issued'
        }
        
        return TicketRepository.create(ticket_data)
    
    @staticmethod
    def get_ticket_by_reservation(reservation_id: int) -> Optional[Ticket]:
        """obtiene el ticket de una reservation"""
        return TicketRepository.get_by_reservation(reservation_id)
    
    @staticmethod
    def _generate_barcode() -> str:
        """genera un codigo de barra unico"""
        return f"TIC-{uuid.uuid4().hex[:12].upper()}"
