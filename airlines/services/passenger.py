"""
Servicio para lógica de negocio de pasajeros.
"""
from typing import Optional, Dict
from django.db import transaction
from django.core.exceptions import ValidationError
from repositories.passenger import PassengerRepository
from apps.passengers.models import Passenger


class PassengerService:
    """Servicio para gestionar la lógica de negocio de pasajeros"""
    
    def __init__(self):
        self.repository = PassengerRepository()
    
    def get_passenger_by_id(self, passenger_id: int) -> Optional[Passenger]:
        """Obtiene un pasajero por ID"""
        return self.repository.get_by_id(passenger_id)
    
    def get_passenger_by_email(self, email: str) -> Optional[Passenger]:
        """Obtiene un pasajero por email"""
        return self.repository.get_by_email(email)
    
    def get_passenger_by_user(self, user) -> Optional[Passenger]:
        """Obtiene un pasajero por usuario"""
        return self.repository.get_by_user(user)
    
    @transaction.atomic
    def create_passenger(self, data: dict, user=None) -> dict:
        """
        Crea un nuevo pasajero con validaciones y devuelve un diccionario de resultado.
        """
        try:
            # Validar que el email no esté en uso
            if self.repository.get_by_email(data.get('email')):
                return {
                    'success': False,
                    'message': 'A passenger with this email already exists.'
                }

            # Validar que el documento no esté en uso
            if self.repository.get_by_document(data.get('document')):
                return {
                    'success': False,
                    'message': 'A passenger with this document already exists.'
                }

            # Asociar usuario si se proporciona
            if user:
                data['user'] = user

            # Crear el pasajero
            passenger = self.repository.create(data)

            return {
                'success': True,
                'message': 'Passenger profile created successfully.',
                'passenger': passenger
            }

        except Exception as e:
            return {
                'success': False,
                'message': f'Error creating passenger: {str(e)}'
            }

    @transaction.atomic
    def update_passenger(self, passenger_id: int, data: dict) -> Passenger:
        """
        Actualiza un pasajero existente con validaciones.
        """
        passenger = self.repository.get_by_id(passenger_id)
        if not passenger:
            raise ValidationError('Passenger not found.')
        
        # Validar email único si cambió
        if 'email' in data and data['email'] != passenger.email:
            existing = self.repository.get_by_email(data['email'])
            if existing and existing.id != passenger.id:
                raise ValidationError('A passenger with this email already exists.')
        
        # Validar documento único si cambió
        if 'document' in data and data['document'] != passenger.document:
            existing = self.repository.get_by_document(data['document'])
            if existing and existing.id != passenger.id:
                raise ValidationError('A passenger with this document already exists.')
        
        return self.repository.update(passenger, data)
    
    def deactivate_passenger(self, passenger_id: int) -> Passenger:
        """Desactiva un pasajero"""
        passenger = self.repository.get_by_id(passenger_id)
        if not passenger:
            raise ValidationError('Passenger not found.')
        
        return self.repository.deactivate(passenger)
    
    def get_passenger_with_stats(self, passenger_id: int) -> Dict:
        """
        Obtiene un pasajero con estadísticas de sus reservas.
        """
        passenger = self.repository.get_with_reservations(passenger_id)
        if not passenger:
            raise ValidationError('Passenger not found.')
        
        reservations = passenger.reservations.all()
        
        return {
            'passenger': passenger,
            'total_reservations': reservations.count(),
            'active_reservations': reservations.filter(status__in=['confirmed', 'paid']).count(),
            'completed_reservations': reservations.filter(status='completed').count(),
            'cancelled_reservations': reservations.filter(status='cancelled').count(),
        }
    
    def search_passengers(self, query: str):
        """Busca pasajeros por nombre, email o documento"""
        return self.repository.search(query)
    
    def get_all_active_passengers(self):
        """Obtiene todos los pasajeros activos"""
        return self.repository.get_all_active()
