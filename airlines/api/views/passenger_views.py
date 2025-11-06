"""
ViewSets para gestión de pasajeros.
"""
from rest_framework import viewsets, status
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from django.core.exceptions import ValidationError

from api.serializers import (
    PassengerSerializer,
    PassengerCreateSerializer,
    PassengerDetailSerializer
)
from api.permissions import IsPassengerOwnerOrAdmin
from services.passenger import PassengerService
from apps.passengers.models import Passenger


class PassengerViewSet(viewsets.ModelViewSet):
    """
    ViewSet para gestión de pasajeros.
    
    list: Listar todos los pasajeros (solo admin)
    retrieve: Obtener detalle de un pasajero
    create: Registrar un nuevo pasajero
    update: Actualizar información de un pasajero
    my_profile: Obtener perfil del pasajero autenticado
    my_reservations: Obtener reservas del pasajero autenticado
    """
    queryset = Passenger.objects.all()
    permission_classes = [IsAuthenticated]
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.service = PassengerService()
    
    def get_serializer_class(self):
        """Seleccionar serializer según la acción"""
        if self.action == 'create':
            return PassengerCreateSerializer
        elif self.action in ['retrieve', 'my_profile']:
            return PassengerDetailSerializer
        return PassengerSerializer
    
    def get_permissions(self):
        """Permisos según la acción"""
        if self.action in ['retrieve', 'update', 'partial_update', 'destroy']:
            return [IsPassengerOwnerOrAdmin()]
        return [IsAuthenticated()]
    
    def list(self, request):
        """Listar todos los pasajeros (solo admin)"""
        if not request.user.is_staff:
            return Response(
                {'error': 'Only administrators can list all passengers'},
                status=status.HTTP_403_FORBIDDEN
            )
        
        try:
            passengers = self.service.get_all_active_passengers()
            serializer = self.get_serializer(passengers, many=True)
            return Response(serializer.data)
        except Exception as e:
            return Response(
                {'error': str(e)},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )
    
    def retrieve(self, request, pk=None):
        """Obtener detalle de un pasajero"""
        try:
            passenger = self.service.get_passenger_by_id(pk)
            if not passenger:
                return Response(
                    {'error': 'Passenger not found'},
                    status=status.HTTP_404_NOT_FOUND
                )
            
            # Verificar permisos
            self.check_object_permissions(request, passenger)
            
            serializer = self.get_serializer(passenger)
            return Response(serializer.data)
        except Exception as e:
            return Response(
                {'error': str(e)},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )
    
    def create(self, request):
        """Registrar un nuevo pasajero"""
        serializer = self.get_serializer(data=request.data)
        if serializer.is_valid():
            try:
                # Asociar con el usuario autenticado si no se especifica
                data = serializer.validated_data
                if 'user' not in data and request.user.is_authenticated:
                    data['user'] = request.user
                
                result = self.service.create_passenger(data)
                
                if result['success']:
                    return Response(
                        PassengerDetailSerializer(result['passenger']).data,
                        status=status.HTTP_201_CREATED
                    )
                else:
                    return Response(
                        {'error': result['message']},
                        status=status.HTTP_400_BAD_REQUEST
                    )
            except Exception as e:
                return Response(
                    {'error': str(e)},
                    status=status.HTTP_500_INTERNAL_SERVER_ERROR
                )
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
    
    def update(self, request, pk=None):
        """Actualizar información de un pasajero"""
        try:
            passenger = self.service.get_passenger_by_id(pk)
            if not passenger:
                return Response(
                    {'error': 'Passenger not found'},
                    status=status.HTTP_404_NOT_FOUND
                )
            
            # Verificar permisos
            self.check_object_permissions(request, passenger)
            
            serializer = PassengerSerializer(data=request.data, partial=True)
            if serializer.is_valid():
                updated_passenger = self.service.update_passenger(
                    pk, serializer.validated_data
                )
                return Response(PassengerDetailSerializer(updated_passenger).data)
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
        except ValidationError as e:
            return Response(
                {'error': str(e)},
                status=status.HTTP_400_BAD_REQUEST
            )
        except Exception as e:
            return Response(
                {'error': str(e)},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )
    
    @action(detail=False, methods=['get'])
    def my_profile(self, request):
        """Obtener perfil del pasajero autenticado"""
        try:
            passenger = self.service.get_passenger_by_user(request.user)
            if not passenger:
                return Response(
                    {'error': 'Passenger profile not found'},
                    status=status.HTTP_404_NOT_FOUND
                )
            
            serializer = self.get_serializer(passenger)
            return Response(serializer.data)
        except Exception as e:
            return Response(
                {'error': str(e)},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )
    
    @action(detail=False, methods=['get'])
    def my_reservations(self, request):
        """Obtener reservas del pasajero autenticado"""
        try:
            passenger = self.service.get_passenger_by_user(request.user)
            if not passenger:
                return Response(
                    {'error': 'Passenger profile not found'},
                    status=status.HTTP_404_NOT_FOUND
                )
            
            from api.serializers import ReservationSerializer
            reservations = passenger.reservations.all().order_by('-reservation_date')
            serializer = ReservationSerializer(reservations, many=True)
            return Response(serializer.data)
        except Exception as e:
            return Response(
                {'error': str(e)},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )
    
    @action(detail=True, methods=['get'])
    def stats(self, request, pk=None):
        """Obtener estadísticas de un pasajero"""
        try:
            passenger = self.service.get_passenger_by_id(pk)
            if not passenger:
                return Response(
                    {'error': 'Passenger not found'},
                    status=status.HTTP_404_NOT_FOUND
                )
            
            # Verificar permisos
            self.check_object_permissions(request, passenger)
            
            stats = self.service.get_passenger_with_stats(pk)
            return Response(stats)
        except Exception as e:
            return Response(
                {'error': str(e)},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )
