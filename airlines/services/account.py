"""
Servicio para la lógica de negocio relacionada con cuentas de usuario.
"""
from typing import Optional, Dict, Any
from django.contrib.auth.models import User
from django.contrib.auth import authenticate
from django.db import transaction

from repositories.account import AccountRepository
from repositories.passenger import PassengerRepository
from repositories.reservation import ReservationRepository


class AccountService:
    """Servicio para gestionar la lógica de negocio de cuentas de usuario."""
    
    def __init__(self):
        self.account_repo = AccountRepository()
        self.passenger_repo = PassengerRepository()
        self.reservation_repo = ReservationRepository() 

    def register_user(self, username: str, email: str, password: str,
                      first_name: str = '', last_name: str = '') -> Dict[str, Any]:
        """
        Registrar un nuevo usuario.
        """
        # Validaciones
        if self.account_repo.username_exists(username):
            return {'success': False, 'user': None, 'message': 'Username already exists.'}
        
        if self.account_repo.email_exists(email):
            return {'success': False, 'user': None, 'message': 'Email already exists.'}
        
        if len(password) < 8:
            return {'success': False, 'user': None, 'message': 'Password must be at least 8 characters long.'}
        
        try:
            with transaction.atomic():
                user = self.account_repo.create_user(
                    username=username,
                    email=email,
                    password=password,
                    first_name=first_name,
                    last_name=last_name
                )
                return {'success': True, 'user': user, 'message': 'User registered successfully.'}
        except Exception as e:
            return {'success': False, 'user': None, 'message': f'Error registering user: {str(e)}'}

    def authenticate_user(self, username: str, password: str) -> Optional[User]:
        """Autenticar un usuario."""
        return authenticate(username=username, password=password)

    def get_user_profile_data(self, user: User) -> Dict[str, Any]:
        """
        Obtener datos del perfil de usuario incluyendo información de pasajero y reservas.
        """
        passenger = self.passenger_repo.get_by_email(user.email)
        
        reservations = []
        if passenger:
            reservations = self.reservation_repo.get_by_passenger(passenger)[:5]
        
        return {
            'user': user,
            'passenger': passenger,
            'reservations': reservations,
            'has_passenger_profile': passenger is not None
        }

    def update_user_profile(self, user: User, **kwargs) -> Dict[str, Any]:
        """Actualizar perfil de usuario."""
        try:
            if 'email' in kwargs and kwargs['email'] != user.email:
                if self.account_repo.email_exists(kwargs['email']):
                    return {'success': False, 'message': 'Email already exists.'}
            
            self.account_repo.update_user(user, **kwargs)
            return {'success': True, 'message': 'Profile updated successfully.'}
        except Exception as e:
            return {'success': False, 'message': f'Error updating profile: {str(e)}'}

    def change_password(self, user: User, old_password: str, new_password: str) -> Dict[str, Any]:
        """Cambiar contraseña de usuario."""
        if not user.check_password(old_password):
            return {'success': False, 'message': 'Current password is incorrect.'}
        
        if len(new_password) < 8:
            return {'success': False, 'message': 'New password must be at least 8 characters long.'}
        
        try:
            self.account_repo.set_password(user, new_password)
            return {'success': True, 'message': 'Password changed successfully.'}
        except Exception as e:
            return {'success': False, 'message': f'Error changing password: {str(e)}'}

    def get_user_dashboard_data(self, user: User) -> Dict[str, Any]:
        """
        Obtener datos para el dashboard del usuario.
        """
        passenger = self.passenger_repo.get_by_email(user.email)
        
        if not passenger:
            return {'has_passenger_profile': False, 'passenger': None}
        
        stats = getattr(self.passenger_repo, "get_passenger_statistics", lambda x: {
            'total_reservations': 0, 'active_reservations': 0, 'completed_reservations': 0
        })(passenger.id)

        upcoming = self.reservation_repo.get_upcoming_by_passenger(passenger, limit=3)
        history = self.reservation_repo.get_history_by_passenger(passenger, limit=5)
        
        return {
            'has_passenger_profile': True,
            'passenger': passenger,
            'total_reservations': stats.get('total_reservations', 0),
            'active_reservations': stats.get('active_reservations', 0),
            'completed_reservations': stats.get('completed_reservations', 0),
            'upcoming_reservations': upcoming,
            'recent_history': history
        }

    def create_user_admin(self, username: str, email: str, password: str,
                          first_name: str = '', last_name: str = '',
                          is_staff: bool = False, is_superuser: bool = False) -> Dict[str, Any]:
        """Crear usuario (admin)."""
        if self.account_repo.username_exists(username):
            return {'success': False, 'user': None, 'message': 'Username already exists.'}
        if self.account_repo.email_exists(email):
            return {'success': False, 'user': None, 'message': 'Email already exists.'}
        
        try:
            user = self.account_repo.create_user(
                username=username,
                email=email,
                password=password,
                first_name=first_name,
                last_name=last_name,
                is_staff=is_staff,
                is_superuser=is_superuser
            )
            return {'success': True, 'user': user, 'message': f'User {username} created successfully.'}
        except Exception as e:
            return {'success': False, 'user': None, 'message': f'Error creating user: {str(e)}'}

    def update_user_admin(self, user_id: int, **kwargs) -> Dict[str, Any]:
        """Actualizar usuario (admin)."""
        user = self.account_repo.get_by_id(user_id)
        if not user:
            return {'success': False, 'message': 'User not found.'}
        
        try:
            if 'email' in kwargs and kwargs['email'] != user.email:
                if self.account_repo.email_exists(kwargs['email']):
                    return {'success': False, 'message': 'Email already exists.'}
            
            self.account_repo.update_user(user, **kwargs)
            return {'success': True, 'message': f'User {user.username} updated successfully.'}
        except Exception as e:
            return {'success': False, 'message': f'Error updating user: {str(e)}'}

    def delete_user_admin(self, user_id: int, current_user: User) -> Dict[str, Any]:
        """Eliminar usuario (admin)."""
        user = self.account_repo.get_by_id(user_id)
        if not user:
            return {'success': False, 'message': 'User not found.'}
        if user.id == current_user.id:
            return {'success': False, 'message': 'You cannot delete your own account.'}
        
        try:
            username = user.username
            self.account_repo.delete_user(user)
            return {'success': True, 'message': f'User {username} deleted successfully.'}
        except Exception as e:
            return {'success': False, 'message': f'Error deleting user: {str(e)}'}

    def search_users(self, search_term: str = ''):
        """Buscar usuarios."""
        if search_term:
            return self.account_repo.search_users(search_term)
        return self.account_repo.get_all_users()

    def check_username_availability(self, username: str) -> bool:
        """Verificar disponibilidad de nombre de usuario."""
        return not self.account_repo.username_exists(username)
