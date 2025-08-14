"""
repositories para la app de pasajeros
"""
from django.db.models import QuerySet
from typing import Optional
from apps.passengers.models import Passenger


class PassengerRepository:
    """repository para manejar cosas de passenger"""
    
    @staticmethod
    def get_all() -> QuerySet[Passenger]:
        """aca trae todos los pasajeros que haya"""
        return Passenger.objects.all()  # esto devuelve un queryset con todos
    
    @staticmethod
    def get_by_id(passenger_id: int) -> Optional[Passenger]:
        """aca busca un pasajero por id"""
        try:
            # busca el passenger por id exacto, si no existe tira error
            return Passenger.objects.get(id=passenger_id)
        except Passenger.DoesNotExist:
            # si no lo encuentra devuelve None en vez de romper
            return None
    
    @staticmethod
    def get_by_document(document: str) -> Optional[Passenger]:
        """aca busca un pasajero por documento"""
        try:
            # aca el campo document tiene que existir en el model
            return Passenger.objects.get(document=document)
        except Passenger.DoesNotExist:
            return None
    
    @staticmethod
    def get_by_email(email: str) -> Optional[Passenger]:
        """aca busca un pasajero por email"""
        try:
            return Passenger.objects.get(email=email)  # busca por coincidencia exacta
        except Passenger.DoesNotExist:
            return None
    
    @staticmethod
    def create(data: dict) -> Passenger:
        """aca crea un pasajero nuevo"""
        # el **data desarma el diccionario y pasa cada clave como argumento
        return Passenger.objects.create(**data)
    
    @staticmethod
    def update(passenger_id: int, data: dict) -> Optional[Passenger]:
        """aca actualiza un pasajero"""
        try:
            passenger = Passenger.objects.get(id=passenger_id)  # primero lo busca
            # recorre los datos y asigna cada uno al objeto passenger
            for key, value in data.items():
                setattr(passenger, key, value)  # setattr asigna dinamicamente
            passenger.save()  # guarda los cambios en la base
            return passenger
        except Passenger.DoesNotExist:
            return None
    
    @staticmethod
    def search_by_name(name: str) -> QuerySet[Passenger]:
        """aca busca pasajeros por nombre"""
        # __icontains hace busqueda sin importar mayus/minus
        return Passenger.objects.filter(name__icontains=name)
