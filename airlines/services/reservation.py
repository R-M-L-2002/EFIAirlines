"""
Servicio para lógica de negocio de reservas y tickets.
"""
from typing import Optional, Dict
from django.db import transaction
from django.core.exceptions import ValidationError
from django.utils import timezone
from datetime import timedelta
from repositories.reservation import ReservationRepository, TicketRepository
from repositories.flight import FlightRepository, SeatRepository
from repositories.passenger import PassengerRepository
from apps.reservations.models import Reservation, Ticket


class ReservationService:
    """Servicio para gestionar la lógica de negocio de reservas"""
    
    def __init__(self):
        self.repository = ReservationRepository()
        self.ticket_repository = TicketRepository()
        self.flight_repository = FlightRepository()
        self.seat_repository = SeatRepository()
        self.passenger_repository = PassengerRepository()
    
    # ================== RESERVAS ==================
    def get_reservation_by_id(self, reservation_id: int) -> Optional[Reservation]:
        return self.repository.get_by_id(reservation_id)
    
    def get_reservation_by_code(self, reservation_code: str) -> Optional[Reservation]:
        return self.repository.get_by_code(reservation_code)
    
    def get_reservations_by_passenger(self, passenger_id: int):
        passenger = self.passenger_repository.get_by_id(passenger_id)
        if not passenger:
            raise ValidationError('Passenger not found.')
        return self.repository.get_by_passenger(passenger)
    
    @transaction.atomic
    def create_reservation(self, flight_id: int, passenger_id: int, seat_id: int, notes: str = '') -> Reservation:
        flight = self.flight_repository.get_by_id(flight_id)
        passenger = self.passenger_repository.get_by_id(passenger_id)
        seat = self.seat_repository.get_by_id(seat_id)

        # Validaciones de vuelo y asiento omitidas por brevedad...

        # Verificar reservas activas (solo las que no estén canceladas)
        existing = self.repository.check_existing_reservation(flight, passenger)
        if existing:
            raise ValidationError(
                f'You already have an active reservation for this flight: {existing.reservation_code}'
            )

        total_price = flight.base_price + seat.extra_price
        reservation_data = {
            'flight': flight,
            'passenger': passenger,
            'seat': seat,
            'status': Reservation.STATUS_PENDING,
            'notes': notes,
            'total_price': total_price,
            'expiration_date': timezone.now() + timedelta(hours=24)
        }

        # Crear la reserva ignorando la restricción unique_together si la reserva anterior fue cancelada
        return Reservation.objects.create(**reservation_data)

    
    @transaction.atomic
    def confirm_reservation(self, reservation_code: str) -> Reservation:
        reservation = self.repository.get_by_code(reservation_code)
        if not reservation:
            raise ValidationError('Reservation not found.')
        if reservation.status != Reservation.STATUS_PENDING:
            raise ValidationError('Only pending reservations can be confirmed.')
        if reservation.is_expired:
            raise ValidationError('This reservation has expired.')
        
        reservation.status = Reservation.STATUS_CONFIRMED
        reservation.save()
        return reservation
    
    @transaction.atomic
    def cancel_reservation(self, reservation_code: str, reason: str = '', comments: str = '') -> Reservation:
        reservation = self.repository.get_by_code(reservation_code)
        if not reservation:
            raise ValidationError('Reservation not found.')
        if not reservation.can_cancel:
            raise ValidationError('This reservation cannot be canceled.')
        
        reservation.status = Reservation.STATUS_CANCELLED
        reservation.cancellation_reason = reason
        reservation.cancellation_comments = comments
        reservation.save()
        return reservation
    
    @transaction.atomic
    def process_payment(self, reservation_code: str, payment_method: str = 'credit_card') -> Dict:
        reservation = self.repository.get_by_code(reservation_code)
        if not reservation:
            raise ValidationError('Reservation not found.')
        if reservation.status not in [Reservation.STATUS_PENDING, Reservation.STATUS_CONFIRMED]:
            raise ValidationError('This reservation has already been paid or canceled.')
        
        reservation.status = Reservation.STATUS_PAID
        reservation.payment_method = payment_method
        reservation.save()
        
        ticket = self.ticket_repository.get_by_reservation(reservation)
        if not ticket:
            ticket = self.ticket_repository.create({
                'reservation': reservation,
                'status': Ticket.TICKET_ISSUED
            })
        
        return {'reservation': reservation, 'ticket': ticket}
    
    def get_available_seats_for_flight(self, flight_id: int) -> Dict:
        flight = self.flight_repository.get_by_id(flight_id)
        if not flight:
            raise ValidationError('Flight not found.')
        
        occupied_seat_ids = self.repository.get_occupied_seats(flight)
        all_seats = self.seat_repository.get_by_airplane(flight.airplane)
        
        seats_by_row = {}
        for seat in all_seats:
            if seat.row not in seats_by_row:
                seats_by_row[seat.row] = []
            seat_price = flight.base_price + seat.extra_price
            is_occupied = seat.id in occupied_seat_ids or seat.status == 'maintenance'
            seats_by_row[seat.row].append({
                'seat': seat,
                'price': seat_price,
                'is_occupied': is_occupied,
                'seat_class': seat.type
            })
        
        available_count = sum(
            1 for row_seats in seats_by_row.values() 
            for seat_info in row_seats 
            if not seat_info['is_occupied']
        )
        
        return {
            'flight': flight,
            'seats_by_row': dict(sorted(seats_by_row.items())),
            'total_available': available_count
        }
    
    def get_passenger_stats(self, passenger_id: int) -> Dict:
        passenger = self.passenger_repository.get_by_id(passenger_id)
        if not passenger:
            raise ValidationError('Passenger not found.')
        
        reservations = self.repository.get_by_passenger(passenger)
        return {
            'total': reservations.count(),
            'pending': reservations.filter(status=Reservation.STATUS_PENDING).count(),
            'confirmed': reservations.filter(status__in=[Reservation.STATUS_CONFIRMED, Reservation.STATUS_PAID]).count(),
            'completed': reservations.filter(status=Reservation.STATUS_COMPLETED).count(),
            'canceled': reservations.filter(status=Reservation.STATUS_CANCELLED).count(),
        }
    
    def get_upcoming_reservations(self, passenger_id: int, limit: int = 3):
        passenger = self.passenger_repository.get_by_id(passenger_id)
        if not passenger:
            raise ValidationError('Passenger not found.')
        return self.repository.get_upcoming_by_passenger(passenger, limit)
    
    def get_reservation_history(self, passenger_id: int, limit: int = 5):
        passenger = self.passenger_repository.get_by_id(passenger_id)
        if not passenger:
            raise ValidationError('Passenger not found.')
        return self.repository.get_history_by_passenger(passenger, limit)


class TicketService:
    """Servicio para gestionar la lógica de negocio de tickets"""
    
    def __init__(self):
        self.repository = TicketRepository()
        self.reservation_repository = ReservationRepository()
    
    def get_ticket_by_barcode(self, barcode: str) -> Optional[Ticket]:
        return self.repository.get_by_barcode(barcode)
    
    def get_ticket_by_reservation_code(self, reservation_code: str) -> Optional[Ticket]:
        reservation = self.reservation_repository.get_by_code(reservation_code)
        if not reservation:
            raise ValidationError('Reservation not found.')
        return self.repository.get_by_reservation(reservation)
