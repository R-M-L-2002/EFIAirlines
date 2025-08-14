"""
repositories para la app de flights
maneja acceso directo a la base de datos
"""
from django.db.models import QuerySet
from typing import Optional, List
from apps.flights.models import Plane, Flight, Seat


class PlaneRepository:
    """repo para manejar planes"""
    
    @staticmethod
    def get_all() -> QuerySet[Plane]:
        """trae todos los planes que hay en la db"""
        return Plane.objects.all()
    
    @staticmethod
    def get_by_id(plane_id: int) -> Optional[Plane]:
        """busca un plane por id, si no existe devuelve None"""
        try:
            return Plane.objects.get(id=plane_id)
        except Plane.DoesNotExist:
            return None
    
    @staticmethod
    def get_by_model(model: str) -> QuerySet[Plane]:
        """busca planes que tengan el modelo parecido al que pasaste"""
        return Plane.objects.filter(model__icontains=model)
    
    @staticmethod
    def create(data: dict) -> Plane:
        """crea un plane nuevo con los datos del dict"""
        return Plane.objects.create(**data)
    
    @staticmethod
    def update(plane_id: int, data: dict) -> Optional[Plane]:
        """actualiza un plane con los valores del dict"""
        try:
            plane = Plane.objects.get(id=plane_id)
            # recorre el dict y pone cada valor en el objeto
            for key, value in data.items():
                setattr(plane, key, value)
            plane.save()  # guarda los cambios en la db
            return plane
        except Plane.DoesNotExist:
            return None


class FlightRepository:
    """repo para manejar flights"""
    
    @staticmethod
    def get_all() -> QuerySet[Flight]:
        """trae todos los flights, trae tambien info del plane para no hacer query extra"""
        return Flight.objects.select_related('plane').all()
    
    @staticmethod
    def get_by_id(flight_id: int) -> Optional[Flight]:
        """busca un flight por id, trae info del plane"""
        try:
            return Flight.objects.select_related('plane').get(id=flight_id)
        except Flight.DoesNotExist:
            return None
    
    @staticmethod
    def get_available() -> QuerySet[Flight]:
        """trae los flights que estan programados, disponibles para reservar"""
        return Flight.objects.filter(status='scheduled').select_related('plane')
    
    @staticmethod
    def search_flights(origin: str = None, destination: str = None, date: str = None) -> QuerySet[Flight]:
        """busca flights segun los filtros que pases"""
        queryset = Flight.objects.select_related('plane')
        
        if origin:
            # si pasaron origen, filtra los que contengan esa palabra
            queryset = queryset.filter(origin__icontains=origin)
        if destination:
            # si pasaron destino, filtra los que contengan esa palabra
            queryset = queryset.filter(destination__icontains=destination)
        if date:
            # si pasaron fecha, filtra por fecha de salida
            queryset = queryset.filter(departure_date__date=date)
            
        return queryset
    
    @staticmethod
    def create(data: dict) -> Flight:
        """crea un flight nuevo con los datos del dict"""
        return Flight.objects.create(**data)


class SeatRepository:
    """repo para manejar seats"""
    
    @staticmethod
    def get_by_flight(flight_id: int) -> QuerySet[Seat]:
        """trae todos los seats de un flight"""
        return Seat.objects.filter(plane__flight__id=flight_id)
    
    @staticmethod
    def get_available_by_flight(flight_id: int) -> QuerySet[Seat]:
        """trae los seats que estan libres en ese flight"""
        return Seat.objects.filter(
            plane__flight__id=flight_id,
            status='available'
        )
    
    @staticmethod
    def get_by_id(seat_id: int) -> Optional[Seat]:
        """busca un seat por id"""
        try:
            return Seat.objects.get(id=seat_id)
        except Seat.DoesNotExist:
            return None
    
    @staticmethod
    def update_status(seat_id: int, new_status: str) -> bool:
        """cambia el estado de un seat, devuelve True si pudo, False si no existe"""
        try:
            seat = Seat.objects.get(id=seat_id)
            seat.status = new_status
            seat.save()  # guarda el cambio en la db
            return True
        except Seat.DoesNotExist:
            return False
