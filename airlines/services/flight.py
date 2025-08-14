"""
services para la app de flights
"""
from typing import Optional, List, Dict
from django.db import transaction
from repositories.flight import PlaneRepository, FlightRepository, SeatRepository
from apps.flights.models import Plane, Flight, Seat


class PlaneService:
    """service para manejar logica de negocio de Plane"""
    
    @staticmethod
    def create_plane_with_seats(data: dict) -> Plane:
        """crea un plane y genera sus seats automaticamente"""
        with transaction.atomic():  # si algo falla se revierte todo
            # primero creamos el plane
            plane = PlaneRepository.create(data)
            
            # despues generamos los seats automaticos
            SeatService.generate_seats_for_plane(plane)
            
            return plane
    
    @staticmethod
    def get_available_planes() -> List[Plane]:
        """trae los planes que estan activos y se pueden asignar a flights"""
        return list(PlaneRepository.get_all().filter(active=True))
    
    @staticmethod
    def get_plane_stats(plane_id: int) -> Optional[Dict]:
        """trae estadisticas de un plane"""
        plane = PlaneRepository.get_by_id(plane_id)
        if not plane:
            return None
        
        total_seats = plane.seat_set.count()
        occupied_seats = plane.seat_set.filter(status='occupied').count()
        
        return {
            'plane': plane,
            'total_seats': total_seats,
            'occupied_seats': occupied_seats,
            'occupancy_percent': (occupied_seats / total_seats * 100) if total_seats > 0 else 0
        }


class FlightService:
    """service para manejar logica de negocio de Flight"""
    
    @staticmethod
    def get_available_flights(origin: str = None, destination: str = None, date: str = None) -> List[Flight]:
        """busca flights disponibles usando filtros"""
        flights = FlightRepository.search_flights(origin, destination, date)
        # filtra los que esten programados
        return list(flights.filter(status='scheduled'))
    
    @staticmethod
    def get_flight_with_seats(flight_id: int) -> Optional[Dict]:
        """trae un flight con info de sus seats"""
        flight = FlightRepository.get_by_id(flight_id)
        if not flight:
            return None
        
        seats = SeatRepository.get_by_flight(flight_id)
        available_seats = SeatRepository.get_available_by_flight(flight_id)
        
        return {
            'flight': flight,
            'seats': seats,
            'available_seats': available_seats.count(),
            'occupied_seats': seats.filter(status='occupied').count()
        }
    
    @staticmethod
    def check_flight_availability(flight_id: int) -> bool:
        """chequea si el flight tiene seats disponibles"""
        available_seats = SeatRepository.get_available_by_flight(flight_id)
        return available_seats.exists()


class SeatService:
    """service para manejar logica de negocio de Seat"""
    
    @staticmethod
    def generate_seats_for_plane(plane: Plane) -> None:
        """genera todos los seats automaticamente para un plane"""
        seats_data = []
        
        for row in range(1, plane.rows + 1):
            for column in range(1, plane.columns + 1):
                # definimos tipo de seat segun la fila
                if row <= 3:
                    seat_type = 'first'
                elif row <= 8:
                    seat_type = 'business'
                else:
                    seat_type = 'economy'
                
                # generamos numero de seat tipo 1A, 1B, 2A, etc
                column_letter = chr(64 + column)  # A, B, C, etc
                number = f"{row}{column_letter}"
                
                seats_data.append(Seat(
                    plane=plane,
                    number=number,
                    row=row,
                    column=column,
                    type=seat_type,
                    status='available'
                ))
        
        # creamos todos los seats de golpe en la db
        Seat.objects.bulk_create(seats_data)
    
    @staticmethod
    def reserve_seat(seat_id: int) -> bool:
        """reserva un seat especifico, devuelve False si ya esta ocupado"""
        seat = SeatRepository.get_by_id(seat_id)
        if not seat or seat.status != 'available':
            return False
        
        return SeatRepository.update_status(seat_id, 'reserved')
    
    @staticmethod
    def release_seat(seat_id: int) -> bool:
        """libera un seat previamente reservado"""
        return SeatRepository.update_status(seat_id, 'available')
