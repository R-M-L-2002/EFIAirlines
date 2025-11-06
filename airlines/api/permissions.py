"""
Permisos personalizados para la API.
"""
from rest_framework import permissions


class IsAdminOrReadOnly(permissions.BasePermission):
    """
    Permiso personalizado: solo administradores pueden crear/editar/eliminar.
    Usuarios autenticados pueden leer.
    """
    
    def has_permission(self, request, view):
        # Permitir lectura a usuarios autenticados
        if request.method in permissions.SAFE_METHODS:
            return request.user and request.user.is_authenticated
        
        # Solo administradores pueden modificar
        return request.user and request.user.is_staff


class IsOwnerOrAdmin(permissions.BasePermission):
    """
    Permiso personalizado: solo el propietario o administrador puede acceder.
    """
    
    def has_object_permission(self, request, view, obj):
        # Administradores tienen acceso total
        if request.user.is_staff:
            return True
        
        # Verificar si el objeto tiene relación con el usuario
        if hasattr(obj, 'user'):
            return obj.user == request.user
        
        if hasattr(obj, 'passenger') and hasattr(obj.passenger, 'user'):
            return obj.passenger.user == request.user
        
        return False


class IsPassengerOwnerOrAdmin(permissions.BasePermission):
    """
    Permiso para pasajeros: solo el propietario o admin.
    """
    
    def has_object_permission(self, request, view, obj):
        # Administradores tienen acceso total
        if request.user.is_staff:
            return True
        
        # El pasajero solo puede ver/editar su propia información
        if hasattr(obj, 'user') and obj.user:
            return obj.user == request.user
        
        return False


class IsReservationOwnerOrAdmin(permissions.BasePermission):
    """
    Permiso para reservas: solo el propietario o admin.
    """
    
    def has_object_permission(self, request, view, obj):
        # Administradores tienen acceso total
        if request.user.is_staff:
            return True
        
        # El pasajero solo puede ver sus propias reservas
        if hasattr(obj, 'passenger') and hasattr(obj.passenger, 'user'):
            return obj.passenger.user == request.user
        
        return False
