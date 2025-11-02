"""
Repositorio para operaciones de datos de Passenger.
Capa de acceso a datos que abstrae las consultas a la base de datos.
"""
from typing import List, Optional
from django.db.models import Q, QuerySet
from django.utils import timezone
from apps.passengers.models import Passenger


class PassengerRepository:
    """Repositorio para gestionar operaciones de datos de pasajeros"""
    
    @staticmethod
    def get_by_id(passenger_id: int) -> Optional[Passenger]:
        """Obtiene un pasajero por su ID"""
        try:
            return Passenger.objects.get(id=passenger_id)
        except Passenger.DoesNotExist:
            return None
    
    @staticmethod
    def get_by_email(email: str) -> Optional[Passenger]:
        """Obtiene un pasajero por su email"""
        try:
            return Passenger.objects.get(email=email)
        except Passenger.DoesNotExist:
            return None
    
    @staticmethod
    def get_by_document(document: str) -> Optional[Passenger]:
        """Obtiene un pasajero por su documento"""
        try:
            return Passenger.objects.get(document=document)
        except Passenger.DoesNotExist:
            return None
    
    @staticmethod
    def get_by_user(user) -> Optional[Passenger]:
        """Obtiene un pasajero por su usuario"""
        try:
            return Passenger.objects.get(user=user)
        except Passenger.DoesNotExist:
            return None
    
    @staticmethod
    def get_all_active() -> QuerySet:
        """Obtiene todos los pasajeros activos"""
        return Passenger.objects.filter(active=True).order_by('name')
    
    @staticmethod
    def get_all() -> QuerySet:
        """Obtiene todos los pasajeros"""
        return Passenger.objects.all().order_by('name')
    
    @staticmethod
    def create(data: dict) -> Passenger:
        """Crea un nuevo pasajero"""
        return Passenger.objects.create(**data)
    
    @staticmethod
    def update(passenger: Passenger, data: dict) -> Passenger:
        """Actualiza un pasajero existente"""
        for key, value in data.items():
            setattr(passenger, key, value)
        passenger.save()
        return passenger
    
    @staticmethod
    def delete(passenger: Passenger) -> None:
        """Elimina un pasajero"""
        passenger.delete()
    
    @staticmethod
    def deactivate(passenger: Passenger) -> Passenger:
        """Desactiva un pasajero (soft delete)"""
        passenger.active = False
        passenger.save()
        return passenger
    
    @staticmethod
    def search(query: str) -> QuerySet:
        """Busca pasajeros por nombre, email o documento"""
        return Passenger.objects.filter(
            Q(name__icontains=query) |
            Q(email__icontains=query) |
            Q(document__icontains=query)
        ).order_by('name')
    
    @staticmethod
    def get_with_reservations(passenger_id: int) -> Optional[Passenger]:
        """Obtiene un pasajero con sus reservas precargadas"""
        try:
            return Passenger.objects.prefetch_related(
                'reservations',
                'reservations__flight',
                'reservations__seat'
            ).get(id=passenger_id)
        except Passenger.DoesNotExist:
            return None
    
    @staticmethod
    def count_active() -> int:
        """Cuenta los pasajeros activos"""
        return Passenger.objects.filter(active=True).count()
