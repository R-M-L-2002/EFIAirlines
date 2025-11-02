"""
Repositorio para operaciones de datos de Flight, Airplane y Seat.
"""
from typing import List, Optional
from datetime import datetime
from django.db.models import Q, QuerySet, Count
from django.utils import timezone
from apps.flights.models import Flight, Airplane, Seat


class FlightRepository:
    """Repositorio para gestionar operaciones de vuelos"""
    
    @staticmethod
    def get_by_id(flight_id: int) -> Optional[Flight]:
        """Obtiene un vuelo por su ID"""
        try:
            return Flight.objects.select_related('airplane').get(id=flight_id)
        except Flight.DoesNotExist:
            return None
    
    @staticmethod
    def get_by_flight_number(flight_number: str) -> Optional[Flight]:
        """Obtiene un vuelo por su número"""
        try:
            return Flight.objects.select_related('airplane').get(flight_number=flight_number)
        except Flight.DoesNotExist:
            return None
    
    @staticmethod
    def get_all_active() -> QuerySet:
        """Obtiene todos los vuelos activos"""
        return Flight.objects.filter(
            is_active=True,
            status__in=['scheduled', 'boarding']
        ).select_related('airplane').order_by('departure_date')
    
    @staticmethod
    def get_all() -> QuerySet:
        """Obtiene todos los vuelos"""
        return Flight.objects.select_related('airplane').order_by('-departure_date')
    
    @staticmethod
    def create(data: dict) -> Flight:
        """Crea un nuevo vuelo"""
        return Flight.objects.create(**data)
    
    @staticmethod
    def update(flight: Flight, data: dict) -> Flight:
        """Actualiza un vuelo existente"""
        for key, value in data.items():
            setattr(flight, key, value)
        flight.save()
        return flight
    
    @staticmethod
    def delete(flight: Flight) -> None:
        """Elimina un vuelo"""
        flight.delete()
    
    @staticmethod
    def search(filters: dict) -> QuerySet:
        """Busca vuelos con filtros múltiples"""
        queryset = Flight.objects.filter(
            status__in=['scheduled', 'boarding'],
            is_active=True
        ).select_related('airplane')
        
        if filters.get('origin'):
            queryset = queryset.filter(origin__icontains=filters['origin'])
        
        if filters.get('destination'):
            queryset = queryset.filter(destination__icontains=filters['destination'])
        
        if filters.get('date_from'):
            queryset = queryset.filter(departure_date__date__gte=filters['date_from'])
        
        if filters.get('date_to'):
            queryset = queryset.filter(departure_date__date__lte=filters['date_to'])
        
        if filters.get('status'):
            queryset = queryset.filter(status=filters['status'])
        
        return queryset.order_by('departure_date')
    
    @staticmethod
    def get_upcoming(limit: int = 5) -> QuerySet:
        """Obtiene los próximos vuelos programados"""
        return Flight.objects.filter(
            status='scheduled',
            departure_date__gte=timezone.now()
        ).select_related('airplane').order_by('departure_date')[:limit]
    
    @staticmethod
    def get_origin_cities() -> List[str]:
        """Obtiene lista de ciudades de origen"""
        return Flight.objects.values_list('origin', flat=True).distinct().order_by('origin')
    
    @staticmethod
    def get_destination_cities() -> List[str]:
        """Obtiene lista de ciudades de destino"""
        return Flight.objects.values_list('destination', flat=True).distinct().order_by('destination')


class AirplaneRepository:
    """Repositorio para gestionar operaciones de aviones"""
    
    @staticmethod
    def get_by_id(airplane_id: int) -> Optional[Airplane]:
        """Obtiene un avión por su ID"""
        try:
            return Airplane.objects.get(id=airplane_id)
        except Airplane.DoesNotExist:
            return None
    
    @staticmethod
    def get_by_registration(registration: str) -> Optional[Airplane]:
        """Obtiene un avión por su matrícula"""
        try:
            return Airplane.objects.get(registration=registration)
        except Airplane.DoesNotExist:
            return None
    
    @staticmethod
    def get_all() -> QuerySet:
        """Obtiene todos los aviones"""
        return Airplane.objects.all().order_by('-created_at')
    
    @staticmethod
    def get_all_active() -> QuerySet:
        """Obtiene todos los aviones activos"""
        return Airplane.objects.filter(active=True).order_by('model')
    
    @staticmethod
    def create(data: dict) -> Airplane:
        """Crea un nuevo avión"""
        return Airplane.objects.create(**data)
    
    @staticmethod
    def update(airplane: Airplane, data: dict) -> Airplane:
        """Actualiza un avión existente"""
        for key, value in data.items():
            setattr(airplane, key, value)
        airplane.save()
        return airplane
    
    @staticmethod
    def delete(airplane: Airplane) -> None:
        """Elimina un avión"""
        airplane.delete()
    
    @staticmethod
    def get_with_seats(airplane_id: int) -> Optional[Airplane]:
        """Obtiene un avión con sus asientos precargados"""
        try:
            return Airplane.objects.prefetch_related('seats').get(id=airplane_id)
        except Airplane.DoesNotExist:
            return None
    
    @staticmethod
    def count_active() -> int:
        """Cuenta los aviones activos"""
        return Airplane.objects.filter(active=True).count()


class SeatRepository:
    
    """Repositorio para gestionar operaciones de asientos"""
    
    @staticmethod
    def get_by_id(seat_id: int) -> Optional[Seat]:
        """Obtiene un asiento por su ID"""
        try:
            return Seat.objects.select_related('airplane').get(id=seat_id)
        except Seat.DoesNotExist:
            return None
    
    @staticmethod
    def get_by_airplane(airplane: Airplane) -> QuerySet:
        """Obtiene todos los asientos de un avión"""
        return Seat.objects.filter(airplane=airplane).order_by('row', 'column')
    
    @staticmethod
    def get_available_by_airplane(airplane: Airplane) -> QuerySet:
        """Obtiene asientos disponibles de un avión"""
        return Seat.objects.filter(
            airplane=airplane,
            status='available'
        ).order_by('row', 'column')
    
    @staticmethod
    def create(data: dict) -> Seat:
        """Crea un nuevo asiento"""
        return Seat.objects.create(**data)
    
    @staticmethod
    def update(seat: Seat, data: dict) -> Seat:
        """Actualiza un asiento existente"""
        for key, value in data.items():
            setattr(seat, key, value)
        seat.save()
        return seat
    
    @staticmethod
    def delete(seat: Seat) -> None:
        """Elimina un asiento"""
        seat.delete()
    
    @staticmethod
    def bulk_create(seats: List[dict]) -> None:
        """Crea múltiples asientos en una sola operación, ignorando duplicados por seat_number."""
        if not seats:
            return
        Seat.objects.bulk_create([Seat(**seat_data) for seat_data in seats], ignore_conflicts=True)
    
    @staticmethod
    def delete_by_airplane(airplane: Airplane) -> None:
        """Elimina todos los asientos de un avión"""
        Seat.objects.filter(airplane=airplane).delete()
