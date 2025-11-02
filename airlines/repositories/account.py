"""
Repositorio para operaciones de datos relacionadas con cuentas de usuario.
"""
from typing import Optional, List
from django.contrib.auth.models import User
from django.db.models import QuerySet, Q


class AccountRepository:
    """Repositorio para gestionar operaciones de datos de usuarios."""
    
    @staticmethod
    def get_by_id(user_id: int) -> Optional[User]:
        """Obtener usuario por ID."""
        try:
            return User.objects.get(id=user_id)
        except User.DoesNotExist:
            return None
    
    @staticmethod
    def get_by_username(username: str) -> Optional[User]:
        """Obtener usuario por nombre de usuario."""
        try:
            return User.objects.get(username=username)
        except User.DoesNotExist:
            return None
    
    @staticmethod
    def get_by_email(email: str) -> Optional[User]:
        """Obtener usuario por email."""
        try:
            return User.objects.get(email=email)
        except User.DoesNotExist:
            return None
    
    @staticmethod
    def username_exists(username: str) -> bool:
        """Verificar si un nombre de usuario ya existe."""
        return User.objects.filter(username=username).exists()
    
    @staticmethod
    def email_exists(email: str) -> bool:
        """Verificar si un email ya existe."""
        return User.objects.filter(email=email).exists()
    
    @staticmethod
    def create_user(username: str, email: str, password: str, 
                   first_name: str = '', last_name: str = '', 
                   is_staff: bool = False, is_superuser: bool = False) -> User:
        """Crear un nuevo usuario."""
        user = User.objects.create_user(
            username=username,
            email=email,
            password=password,
            first_name=first_name,
            last_name=last_name,
            is_staff=is_staff,
            is_superuser=is_superuser
        )
        return user
    
    @staticmethod
    def update_user(user: User, **kwargs) -> User:
        """Actualizar información de usuario."""
        for key, value in kwargs.items():
            if hasattr(user, key):
                setattr(user, key, value)
        user.save()
        return user
    
    @staticmethod
    def delete_user(user: User) -> None:
        """Eliminar un usuario."""
        user.delete()
    
    @staticmethod
    def get_all_users() -> QuerySet:
        """Obtener todos los usuarios."""
        return User.objects.all().order_by('-date_joined')
    
    @staticmethod
    def search_users(search_term: str) -> QuerySet:
        """Buscar usuarios por nombre de usuario, email, nombre o apellido."""
        return User.objects.filter(
            Q(username__icontains=search_term) |
            Q(email__icontains=search_term) |
            Q(first_name__icontains=search_term) |
            Q(last_name__icontains=search_term)
        ).order_by('-date_joined')
    
    @staticmethod
    def get_staff_users() -> QuerySet:
        """Obtener todos los usuarios staff."""
        return User.objects.filter(is_staff=True).order_by('-date_joined')
    
    @staticmethod
    def get_superusers() -> QuerySet:
        """Obtener todos los superusuarios."""
        return User.objects.filter(is_superuser=True).order_by('-date_joined')
    
    @staticmethod
    def count_total_users() -> int:
        """Contar el total de usuarios."""
        return User.objects.count()
    
    @staticmethod
    def set_password(user: User, new_password: str) -> User:
        """Cambiar la contraseña de un usuario."""
        user.set_password(new_password)
        user.save()
        return user
