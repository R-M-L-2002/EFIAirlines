"""
ViewSets para gestión de vuelos, aviones y asientos.
"""
from rest_framework import viewsets, status
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from django.core.exceptions import ValidationError

from api.serializers import (
    FlightSerializer,
    FlightListSerializer,
    FlightDetailSerializer,
    AirplaneSerializer,
    SeatSerializer
)
from api.permissions import IsAdminOrReadOnly
from services.flight import FlightService, AirplaneService
from repositories.flight import SeatRepository
from apps.flights.models import Flight, Airplane, Seat


class FlightViewSet(viewsets.ModelViewSet):
    """
    ViewSet para gestión de vuelos.
    
    list: Listar todos los vuelos disponibles
    retrieve: Obtener detalle de un vuelo
    create: Crear un nuevo vuelo (solo admin)
    update: Actualizar un vuelo (solo admin)
    destroy: Eliminar un vuelo (solo admin)
    search: Filtrar vuelos por origen, destino y fecha
    """
    queryset = Flight.objects.all()
    permission_classes = [IsAdminOrReadOnly]
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.service = FlightService()
    
    def get_serializer_class(self):
        """Seleccionar serializer según la acción"""
        if self.action == 'list':
            return FlightListSerializer
        elif self.action == 'retrieve':
            return FlightDetailSerializer
        return FlightSerializer
    
    def list(self, request):
        """Listar todos los vuelos activos"""
        try:
            flights = self.service.get_upcoming_flights(limit=100)
            serializer = self.get_serializer(flights, many=True)
            return Response(serializer.data)
        except Exception as e:
            return Response(
                {'error': str(e)},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )
    
    def retrieve(self, request, pk=None):
        """Obtener detalle de un vuelo"""
        try:
            flight = self.service.get_flight_by_id(pk)
            if not flight:
                return Response(
                    {'error': 'Flight not found'},
                    status=status.HTTP_404_NOT_FOUND
                )
            serializer = self.get_serializer(flight)
            return Response(serializer.data)
        except Exception as e:
            return Response(
                {'error': str(e)},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )
    
    def create(self, request):
        """Crear un nuevo vuelo (solo admin)"""
        serializer = self.get_serializer(data=request.data)
        if serializer.is_valid():
            try:
                flight = self.service.create_flight(serializer.validated_data)
                return Response(
                    FlightDetailSerializer(flight).data,
                    status=status.HTTP_201_CREATED
                )
            except ValidationError as e:
                return Response(
                    {'error': str(e)},
                    status=status.HTTP_400_BAD_REQUEST
                )
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
    
    def update(self, request, pk=None):
        """Actualizar un vuelo (solo admin)"""
        serializer = self.get_serializer(data=request.data, partial=True)
        if serializer.is_valid():
            try:
                flight = self.service.update_flight(pk, serializer.validated_data)
                return Response(FlightDetailSerializer(flight).data)
            except ValidationError as e:
                return Response(
                    {'error': str(e)},
                    status=status.HTTP_400_BAD_REQUEST
                )
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
    
    def destroy(self, request, pk=None):
        """Eliminar un vuelo (solo admin)"""
        try:
            self.service.delete_flight(pk)
            return Response(status=status.HTTP_204_NO_CONTENT)
        except ValidationError as e:
            return Response(
                {'error': str(e)},
                status=status.HTTP_400_BAD_REQUEST
            )
    
    @action(detail=False, methods=['get'])
    def search(self, request):
        """
        Filtrar vuelos por origen, destino y fecha.
        Query params: origin, destination, date_from, date_to
        """
        filters = {
            'origin': request.query_params.get('origin'),
            'destination': request.query_params.get('destination'),
            'date_from': request.query_params.get('date_from'),
            'date_to': request.query_params.get('date_to'),
        }
        
        # Remover filtros vacíos
        filters = {k: v for k, v in filters.items() if v}
        
        try:
            flights = self.service.search_flights(filters)
            serializer = FlightListSerializer(flights, many=True)
            return Response(serializer.data)
        except Exception as e:
            return Response(
                {'error': str(e)},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )
    
    @action(detail=False, methods=['get'])
    def cities(self, request):
        """Obtener ciudades de origen y destino disponibles"""
        try:
            cities = self.service.get_available_cities()
            return Response(cities)
        except Exception as e:
            return Response(
                {'error': str(e)},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )


class AirplaneViewSet(viewsets.ModelViewSet):
    """
    ViewSet para gestión de aviones.
    
    list: Listar todos los aviones
    retrieve: Obtener detalle de un avión con layout de asientos
    create: Crear un nuevo avión (solo admin)
    update: Actualizar un avión (solo admin)
    destroy: Eliminar un avión (solo admin)
    """
    queryset = Airplane.objects.all()
    serializer_class = AirplaneSerializer
    permission_classes = [IsAdminOrReadOnly]
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.service = AirplaneService()
    
    def list(self, request):
        """Listar todos los aviones"""
        try:
            airplanes = self.service.get_all_airplanes()
            serializer = self.get_serializer(airplanes, many=True)
            return Response(serializer.data)
        except Exception as e:
            return Response(
                {'error': str(e)},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )
    
    def retrieve(self, request, pk=None):
        """Obtener detalle de un avión con layout de asientos"""
        try:
            airplane_data = self.service.get_airplane_with_layout(pk)
            
            # Serializar el avión
            airplane_serializer = self.get_serializer(airplane_data['airplane'])
            
            # Serializar los asientos por fila
            seats_by_row = {}
            for row, seats in airplane_data['seat_layout'].items():
                seats_by_row[row] = SeatSerializer(seats, many=True).data
            
            response_data = {
                'airplane': airplane_serializer.data,
                'seat_layout': seats_by_row,
                'seat_stats': airplane_data['seat_stats'],
                'status_stats': airplane_data['status_stats'],
                'total_seats': airplane_data['total_seats']
            }
            
            return Response(response_data)
        except ValidationError as e:
            return Response(
                {'error': str(e)},
                status=status.HTTP_404_NOT_FOUND
            )
        except Exception as e:
            return Response(
                {'error': str(e)},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )
    
    def create(self, request):
        """Crear un nuevo avión (solo admin)"""
        serializer = self.get_serializer(data=request.data)
        if serializer.is_valid():
            try:
                airplane = self.service.create_airplane(serializer.validated_data)
                return Response(
                    self.get_serializer(airplane).data,
                    status=status.HTTP_201_CREATED
                )
            except ValidationError as e:
                return Response(
                    {'error': str(e)},
                    status=status.HTTP_400_BAD_REQUEST
                )
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
    
    def update(self, request, pk=None):
        """Actualizar un avión (solo admin)"""
        serializer = self.get_serializer(data=request.data, partial=True)
        if serializer.is_valid():
            try:
                airplane = self.service.update_airplane(pk, serializer.validated_data)
                return Response(self.get_serializer(airplane).data)
            except ValidationError as e:
                return Response(
                    {'error': str(e)},
                    status=status.HTTP_400_BAD_REQUEST
                )
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
    
    def destroy(self, request, pk=None):
        """Eliminar un avión (solo admin)"""
        try:
            self.service.delete_airplane(pk)
            return Response(status=status.HTTP_204_NO_CONTENT)
        except ValidationError as e:
            return Response(
                {'error': str(e)},
                status=status.HTTP_400_BAD_REQUEST
            )


class SeatViewSet(viewsets.ReadOnlyModelViewSet):
    """
    ViewSet para consultar asientos.
    Solo lectura - los asientos se gestionan a través de aviones.
    
    list: Listar todos los asientos
    retrieve: Obtener detalle de un asiento
    by_airplane: Obtener asientos de un avión específico
    """
    queryset = Seat.objects.all()
    serializer_class = SeatSerializer
    permission_classes = [IsAuthenticated]
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.repository = SeatRepository()
    
    @action(detail=False, methods=['get'])
    def by_airplane(self, request):
        """
        Obtener asientos de un avión específico.
        Query param: airplane_id
        """
        airplane_id = request.query_params.get('airplane_id')
        
        if not airplane_id:
            return Response(
                {'error': 'airplane_id is required'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        try:
            from apps.flights.models import Airplane
            airplane = Airplane.objects.get(id=airplane_id)
            seats = self.repository.get_by_airplane(airplane)
            serializer = self.get_serializer(seats, many=True)
            return Response(serializer.data)
        except Airplane.DoesNotExist:
            return Response(
                {'error': 'Airplane not found'},
                status=status.HTTP_404_NOT_FOUND
            )
        except Exception as e:
            return Response(
                {'error': str(e)},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )
    
    @action(detail=False, methods=['get'])
    def check_availability(self, request):
        """
        Verificar disponibilidad de un asiento en un vuelo.
        Query params: seat_id, flight_id
        """
        seat_id = request.query_params.get('seat_id')
        flight_id = request.query_params.get('flight_id')
        
        if not seat_id or not flight_id:
            return Response(
                {'error': 'seat_id and flight_id are required'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        try:
            from apps.reservations.models import Reservation
            
            # Verificar si el asiento está reservado en ese vuelo
            is_reserved = Reservation.objects.filter(
                flight_id=flight_id,
                seat_id=seat_id,
                status__in=['confirmed', 'paid']
            ).exists()
            
            seat = self.repository.get_by_id(seat_id)
            
            return Response({
                'seat_id': seat_id,
                'flight_id': flight_id,
                'is_available': not is_reserved and seat.status == 'available',
                'seat_status': seat.status if seat else None
            })
        except Exception as e:
            return Response(
                {'error': str(e)},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )
