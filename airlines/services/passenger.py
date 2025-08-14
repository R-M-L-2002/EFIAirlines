"""
services para la app de passengers 
"""
from typing import Optional, Dict
from repositories.passenger import PassengerRepository
from apps.passengers.models import Passenger


class PassengerService:
    """service para manejar la logica de negocio de passenger"""
    
    @staticmethod
    def create_passenger(data: dict) -> Optional[Passenger]:
        """crea un passenger nuevo con validaciones previas"""
        # primero chequea que no haya otro con el mismo documento
        if PassengerRepository.get_by_document(data.get('document')):
            raise ValueError("ya existe un passenger con este documento")
        
        # despues chequea que no haya otro con el mismo email
        if PassengerRepository.get_by_email(data.get('email')):
            raise ValueError("ya existe un passenger con este email")
        
        # si paso las validaciones lo crea
        return PassengerRepository.create(data)
    
    @staticmethod
    def get_passenger_history(passenger_id: int) -> Optional[Dict]:
        """trae el historial de reservas de un passenger"""
        # import aca adentro para evitar dependencia circular entre apps
        from repositories.reservation import ReservationRepository
        
        passenger = PassengerRepository.get_by_id(passenger_id)  
        # si no existe, chau
        if not passenger:
            return None
        
        # trae todas las reservas asociadas a ese passenger
        reservations = ReservationRepository.get_by_passenger(passenger_id)
        
        # devuelve un diccionario con todo el resumen
        return {
            'passenger': passenger,
            'total_reservations': reservations.count(),  # cuantas reservas tiene
            'active_reservations': reservations.filter(status='confirmed').count(),  # cuantas estan confirmadas
            'reservations': reservations  # lista completa de reservas
        }
    
    @staticmethod
    def update_passenger(passenger_id: int, data: dict) -> Optional[Passenger]:
        """actualiza un passenger con validaciones"""
        current_passenger = PassengerRepository.get_by_id(passenger_id)
        # si no existe, no se actualiza nada
        if not current_passenger:
            return None
        
        # si en el data hay un documento distinto al actual, valida que no exista otro igual
        if 'document' in data and data['document'] != current_passenger.document:
            if PassengerRepository.get_by_document(data['document']):
                raise ValueError("ya existe un passenger con este documento")
        
        # si en el data hay un email distinto al actual, valida que no exista otro igual
        if 'email' in data and data['email'] != current_passenger.email:
            if PassengerRepository.get_by_email(data['email']):
                raise ValueError("ya existe un passenger con este email")
        
        # si paso las validaciones, actualiza
        return PassengerRepository.update(passenger_id, data)
