"""
Servicio para la lógica de negocio relacionada con reportes y análisis.
"""
from typing import Dict, Any, List
from datetime import datetime, timedelta
from django.utils import timezone
from django.db.models import Count, Sum, Avg, Q

from repositories.flight import FlightRepository
from repositories.passenger import PassengerRepository
from repositories.reservation import ReservationRepository
from repositories.account import AccountRepository


class ReportService:
    """Servicio para generar reportes y análisis del sistema."""
    
    def __init__(self):
        self.flight_repo = FlightRepository()
        self.passenger_repo = PassengerRepository()
        self.reservation_repo = ReservationRepository()
        self.account_repo = AccountRepository()
    
    def get_dashboard_statistics(self) -> Dict[str, Any]:
        """
        Obtener estadísticas generales para el dashboard de reportes.
        
        Returns:
            Dict con estadísticas generales del sistema
        """
        # Estadísticas básicas
        total_flights = self.flight_repo.count_all()
        total_passengers = self.passenger_repo.count_all()
        total_reservations = self.reservation_repo.count_all()
        total_users = self.account_repo.count_total_users()
        
        # Reservas por estado
        reservations_by_status = self.reservation_repo.get_reservations_by_status()
        
        # Vuelos más populares
        popular_flights = self.flight_repo.get_most_popular_flights(limit=5)
        
        # Ingresos mensuales (últimos 6 meses)
        six_months_ago = timezone.now() - timedelta(days=180)
        monthly_income = self.reservation_repo.get_income_by_period(
            start_date=six_months_ago
        )
        
        # Ocupación de vuelos
        flight_occupancy = self._calculate_flight_occupancy(limit=10)
        
        # Pasajeros frecuentes
        frequent_passengers = self.passenger_repo.get_frequent_passengers(limit=5)
        
        return {
            'total_flights': total_flights,
            'total_passengers': total_passengers,
            'total_reservations': total_reservations,
            'total_users': total_users,
            'reservations_by_status': reservations_by_status,
            'popular_flights': popular_flights,
            'monthly_income': monthly_income,
            'flight_occupancy': flight_occupancy,
            'frequent_passengers': frequent_passengers
        }
    
    def get_flight_passengers_report(self, flight_id: int) -> Dict[str, Any]:
        """
        Generar reporte detallado de pasajeros de un vuelo específico.
        
        Args:
            flight_id: ID del vuelo
            
        Returns:
            Dict con información detallada del vuelo y sus pasajeros
        """
        flight = self.flight_repo.get_by_id(flight_id)
        
        if not flight:
            return {
                'success': False,
                'message': 'Flight not found.'
            }
        
        # Obtener reservas del vuelo
        reservations = self.reservation_repo.get_by_flight(flight_id)
        
        # Estadísticas del vuelo
        total_reservations = len(reservations)
        confirmed_reservations = len([
            r for r in reservations 
            if r.status in ['confirmed', 'paid']
        ])
        
        total_income = sum(
            r.total_price for r in reservations 
            if r.status in ['confirmed', 'paid']
        )
        
        # Distribución por tipo de asiento
        seat_distribution = {}
        for reservation in reservations:
            if reservation.status in ['confirmed', 'paid']:
                seat_type = reservation.seat.get_type_display()
                seat_distribution[seat_type] = seat_distribution.get(seat_type, 0) + 1
        
        # Calcular porcentaje de ocupación
        capacity = flight.airplane.capacity
        occupancy_percent = round(
            (confirmed_reservations / capacity * 100), 1
        ) if capacity > 0 else 0
        
        return {
            'success': True,
            'flight': flight,
            'reservations': reservations,
            'total_reservations': total_reservations,
            'confirmed_reservations': confirmed_reservations,
            'total_income': total_income,
            'seat_distribution': seat_distribution,
            'occupancy_percent': occupancy_percent
        }
    
    def get_income_report(self, start_date: datetime = None, end_date: datetime = None):
        """
        Generar reporte detallado de ingresos por período.
        
        Args:
            start_date: Fecha de inicio (default: hace 30 días)
            end_date: Fecha de fin (default: hoy)
            
        Returns:
            Dict con análisis de ingresos del período
        """
        # Fechas por defecto
        if not start_date:
            start_date = timezone.now() - timedelta(days=30)
        if not end_date:
            end_date = timezone.now()

        # Obtener reservas del período
        reservations = self.reservation_repo.get_by_date_range(
            start_date=start_date,
            end_date=end_date,
            status=['confirmed', 'paid']
        )

        # Estadísticas generales
        total_income = sum(r.total_price for r in reservations)
        total_reservations = len(reservations)
        average_income = total_income / total_reservations if total_reservations > 0 else 0

        # Ingresos por día
        daily_income = self._calculate_daily_income(reservations)

        # Ingresos por tipo de asiento
        income_by_type = self._calculate_income_by_seat_type(reservations)

        return {
            'start_date': start_date,
            'end_date': end_date,
            'total_income': total_income,
            'total_reservations': total_reservations,
            'average_income': round(average_income, 2),
            'daily_income': daily_income,
            'income_by_type': income_by_type
        }

    
    def export_reservations_data(self) -> List[Dict[str, Any]]:
        """
        Exportar datos de todas las reservas.
        
        Returns:
            Lista de dicts con información de reservas
        """
        reservations = self.reservation_repo.get_all()
        
        data = []
        for reservation in reservations:
            data.append({
                'code': reservation.reservation_code,
                'flight': f"{reservation.flight.origin} - {reservation.flight.destination}",
                'passenger': reservation.passenger.name,
                'document': f"{reservation.passenger.document_type}: {reservation.passenger.document}",
                'seat': reservation.seat.seat_number,
                'status': reservation.get_status_display(),
                'price': reservation.total_price,
                'reservation_date': reservation.reservation_date.strftime('%d/%m/%Y %H:%M'),
                'origin': reservation.flight.origin,
                'destination': reservation.flight.destination
            })
        
        return data
    
    def export_passengers_data(self) -> List[Dict[str, Any]]:
        """
        Exportar datos de todos los pasajeros.
        
        Returns:
            Lista de dicts con información de pasajeros
        """
        passengers = self.passenger_repo.get_all()
        
        data = []
        for passenger in passengers:
            stats = self.passenger_repo.get_passenger_statistics(passenger.id)
            
            data.append({
                'name': passenger.name,
                'document': f"{passenger.document_type}: {passenger.document}",
                'email': passenger.email,
                'phone': passenger.phone,
                'birthdate': passenger.birth_date.strftime('%d/%m/%Y'),
                'age': passenger.age,
                'total_flights': stats['completed_reservations']
            })
        
        return data
    
    def export_flights_data(self) -> List[Dict[str, Any]]:
        """
        Exportar datos de todos los vuelos.
        
        Returns:
            Lista de dicts con información de vuelos
        """
        flights = self.flight_repo.get_all()
        
        data = []
        for flight in flights:
            reservations_count = self.reservation_repo.count_by_flight(flight.id)
            
            data.append({
                'origin': flight.origin,
                'destination': flight.destination,
                'departure_date': flight.departure_date.strftime('%d/%m/%Y %H:%M'),
                'arrival_date': flight.arrival_date.strftime('%d/%m/%Y %H:%M'),
                'duration': flight.duration,
                'airplane': flight.airplane.model,
                'capacity': flight.airplane.capacity,
                'reservations': reservations_count,
                'status': flight.get_status_display(),
                'base_price': flight.base_price
            })
        
        return data
    
    # Métodos auxiliares privados
    
    def _calculate_flight_occupancy(self, limit: int = 10) -> List[Dict[str, Any]]:
        """Calcular porcentaje de ocupación de vuelos."""
        flights = self.flight_repo.get_all()[:limit]
        
        occupancy_data = []
        for flight in flights:
            total_seats = flight.airplane.capacity
            occupied_seats = self.reservation_repo.count_by_flight(
                flight.id,
                status=['confirmed', 'paid']
            )
            
            percent = (occupied_seats / total_seats * 100) if total_seats > 0 else 0
            
            occupancy_data.append({
                'flight': flight,
                'occupancy': round(percent, 1)
            })
        
        return occupancy_data
    
    def _calculate_daily_income(self, reservations) -> List[Dict[str, Any]]:
        """Calcular ingresos diarios de una lista de reservas."""
        daily_data = {}
        
        for reservation in reservations:
            date_key = reservation.reservation_date.date()
            
            if date_key not in daily_data:
                daily_data[date_key] = {
                    'date': date_key,
                    'total': 0,
                    'count': 0
                }
            
            daily_data[date_key]['total'] += reservation.total_price
            daily_data[date_key]['count'] += 1
        
        return sorted(daily_data.values(), key=lambda x: x['date'])
    
    def _calculate_income_by_seat_type(self, reservations) -> List[Dict[str, Any]]:
        """Calcular ingresos por tipo de asiento."""
        type_data = {}
        
        for reservation in reservations:
            seat_type = reservation.seat.type
            
            if seat_type not in type_data:
                type_data[seat_type] = {
                    'seat_type': seat_type,
                    'total': 0,
                    'count': 0
                }
            
            type_data[seat_type]['total'] += reservation.total_price
            type_data[seat_type]['count'] += 1
        
        return sorted(
            type_data.values(), 
            key=lambda x: x['total'], 
            reverse=True
        )
