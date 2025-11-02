"""
Servicio para lógica de negocio de vuelos, aviones y asientos.
"""
from typing import Optional, Dict, List
from django.db import transaction
from django.core.exceptions import ValidationError
from django.utils import timezone
from repositories.flight import FlightRepository, AirplaneRepository, SeatRepository
from apps.flights.models import Flight, Airplane, Seat


class FlightService:
    """Servicio para gestionar la lógica de negocio de vuelos"""
    
    def __init__(self):
        self.repository = FlightRepository()
    
    def get_flight_by_id(self, flight_id: int) -> Optional[Flight]:
        """Obtiene un vuelo por ID"""
        return self.repository.get_by_id(flight_id)
    
    def get_flight_by_number(self, flight_number: str) -> Optional[Flight]:
        """Obtiene un vuelo por número"""
        return self.repository.get_by_flight_number(flight_number)
    
    @transaction.atomic
    def create_flight(self, data: dict) -> Flight:
        """
        Crea un nuevo vuelo con validaciones.
        """
        # Validar que el número de vuelo no exista
        if self.repository.get_by_flight_number(data.get('flight_number')):
            raise ValidationError('A flight with this number already exists.')
        
        # Validar fechas
        if data.get('departure_date') >= data.get('arrival_date'):
            raise ValidationError('Arrival date must be after departure date.')
        
        # Validar que la fecha de salida sea futura
        if data.get('departure_date') <= timezone.now():
            raise ValidationError('Departure date must be in the future.')
        
        return self.repository.create(data)
    
    @transaction.atomic
    def update_flight(self, flight_id: int, data: dict) -> Flight:
        """Actualiza un vuelo existente"""
        flight = self.repository.get_by_id(flight_id)
        if not flight:
            raise ValidationError('Flight not found.')
        
        # Validar fechas si se actualizan
        departure = data.get('departure_date', flight.departure_date)
        arrival = data.get('arrival_date', flight.arrival_date)
        
        if departure >= arrival:
            raise ValidationError('Arrival date must be after departure date.')
        
        return self.repository.update(flight, data)
    
    def delete_flight(self, flight_id: int) -> None:
        """Elimina un vuelo"""
        flight = self.repository.get_by_id(flight_id)
        if not flight:
            raise ValidationError('Flight not found.')
        
        # Verificar que no tenga reservas activas
        if flight.reservations.filter(status__in=['confirmed', 'paid']).exists():
            raise ValidationError('Cannot delete a flight with active reservations.')
        
        self.repository.delete(flight)
    
    def search_flights(self, filters: dict):
        """Busca vuelos con filtros"""
        return self.repository.search(filters)
    
    def get_upcoming_flights(self, limit: int = 5):
        """Obtiene próximos vuelos"""
        return self.repository.get_upcoming(limit)
    
    def get_available_cities(self) -> Dict[str, List[str]]:
        """Obtiene ciudades de origen y destino disponibles"""
        return {
            'origins': list(self.repository.get_origin_cities()),
            'destinations': list(self.repository.get_destination_cities())
        }
    
    def toggle_flight_active(self, flight_id: int) -> Flight:
        """Activa o desactiva un vuelo"""
        flight = self.repository.get_by_id(flight_id)
        if not flight:
            raise ValidationError('Flight not found.')
        
        flight.is_active = not flight.is_active
        flight.save()
        return flight


class AirplaneService:
    """Servicio para gestionar la lógica de negocio de aviones"""
    
    def __init__(self):
        self.repository = AirplaneRepository()
        self.seat_repository = SeatRepository()
    
    def get_airplane_by_id(self, airplane_id: int) -> Optional[Airplane]:
        """Obtiene un avión por ID"""
        return self.repository.get_by_id(airplane_id)
    
    @transaction.atomic
    def create_airplane(self, data: dict) -> Airplane:
        """
        Crea un nuevo avión y genera sus asientos automáticamente.
        """
        # Validar matrícula única si se proporciona
        if data.get('registration'):
            if self.repository.get_by_registration(data['registration']):
                raise ValidationError('An airplane with this registration already exists.')
        
        # Validar capacidad
        rows = data.get('rows', 0)
        columns = data.get('columns', 0)
        capacity = data.get('capacity', 0)
        
        if rows * columns != capacity:
            raise ValidationError('Capacity must equal rows × columns.')
        
        # Crear el avión
        airplane = self.repository.create(data)
        
        # Generar asientos
        self._create_seats_for_airplane(airplane)
        
        return airplane
    
    @transaction.atomic
    def update_airplane(self, airplane_id: int, data: dict) -> Airplane:
        """Actualiza un avión existente"""
        airplane = self.repository.get_by_id(airplane_id)
        if not airplane:
            raise ValidationError('Airplane not found.')
        
        old_rows = airplane.rows
        old_columns = airplane.columns
        
        # Actualizar el avión
        airplane = self.repository.update(airplane, data)
        
        # Si cambiaron filas o columnas, regenerar asientos
        if old_rows != airplane.rows or old_columns != airplane.columns:
            self.seat_repository.delete_by_airplane(airplane)
            self._create_seats_for_airplane(airplane)
        
        return airplane
    
    def delete_airplane(self, airplane_id: int) -> None:
        """Elimina un avión"""
        airplane = self.repository.get_by_id(airplane_id)
        if not airplane:
            raise ValidationError('Airplane not found.')
        
        # Verificar que no tenga vuelos activos
        if airplane.flights.filter(is_active=True).exists():
            raise ValidationError('Cannot delete an airplane with active flights.')
        
        self.repository.delete(airplane)
    
    def toggle_airplane_active(self, airplane_id: int) -> Airplane:
        """Activa o desactiva un avión"""
        airplane = self.repository.get_by_id(airplane_id)
        if not airplane:
            raise ValidationError('Airplane not found.')
        
        airplane.active = not airplane.active
        airplane.save()
        return airplane
    
    def get_airplane_with_layout(self, airplane_id: int) -> Dict:
        """Obtiene un avión con el layout de asientos organizado"""
        airplane = self.repository.get_with_seats(airplane_id)
        if not airplane:
            raise ValidationError('Airplane not found.')
        
        seats = self.seat_repository.get_by_airplane(airplane)
        
        # Organizar asientos por fila
        seat_layout = {}
        for seat in seats:
            if seat.row not in seat_layout:
                seat_layout[seat.row] = []
            seat_layout[seat.row].append(seat)
        
        # Estadísticas
        seat_stats = {
            'first': seats.filter(type='first').count(),
            'business': seats.filter(type='business').count(),
            'economy': seats.filter(type='economy').count(),
        }
        
        status_stats = {
            'available': seats.filter(status='available').count(),
            'reserved': seats.filter(status='reserved').count(),
            'occupied': seats.filter(status='occupied').count(),
            'maintenance': seats.filter(status='maintenance').count(),
        }
        
        return {
            'airplane': airplane,
            'seat_layout': dict(sorted(seat_layout.items())),
            'seat_stats': seat_stats,
            'status_stats': status_stats,
            'total_seats': seats.count()
        }
    
    def _create_seats_for_airplane(self, airplane: Airplane) -> None:
        """Crea asientos para un avión según su configuración, evitando duplicados."""
        letters = "ABCDEFGHIJKLMNOPQRSTUVWXYZ"
        seats_to_create = []

        # Obtener los asientos existentes para no duplicar
        existing_seat_numbers = set(
            Seat.objects.filter(airplane=airplane).values_list('seat_number', flat=True)
        )

        for row in range(1, airplane.rows + 1):
            for col_index in range(airplane.columns):
                if col_index >= len(letters):
                    continue

                seat_number = f"{row}{letters[col_index]}"

                if seat_number in existing_seat_numbers:
                    continue  # Evitar duplicados

                # Asignar tipo y precio según la fila
                if row <= 2:
                    seat_type = "first"
                    price = 300
                elif row <= 5:
                    seat_type = "business"
                    price = 200
                else:
                    seat_type = "economy"
                    price = 100

                seats_to_create.append({
                    'airplane': airplane,
                    'seat_number': seat_number,
                    'row': row,
                    'column': letters[col_index],
                    'type': seat_type,
                    'status': 'available',
                    'extra_price': price
                })

        if seats_to_create:
            self.seat_repository.bulk_create(seats_to_create)
        
    def get_all_airplanes(self):
        """Obtiene todos los aviones"""
        return self.repository.get_all()
    
    def get_all_active_airplanes(self):
        """Obtiene todos los aviones activos"""
        return self.repository.get_all_active()
