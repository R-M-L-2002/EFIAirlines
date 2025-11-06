"""
ViewSets para gestión de reservas y tickets.
"""
from rest_framework import viewsets, status
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from django.core.exceptions import ValidationError

from api.serializers import (
    ReservationSerializer,
    ReservationCreateSerializer,
    ReservationDetailSerializer,
    TicketSerializer
)
from api.permissions import IsReservationOwnerOrAdmin
from services.reservation import ReservationService, TicketService
from apps.reservations.models import Reservation, Ticket


class ReservationViewSet(viewsets.ModelViewSet):
    """
    ViewSet para gestión de reservas.
    
    list: Listar todas las reservas (admin) o del usuario autenticado
    retrieve: Obtener detalle de una reserva
    create: Crear una nueva reserva
    confirm: Confirmar una reserva
    cancel: Cancelar una reserva
    process_payment: Procesar pago de una reserva
    available_seats: Obtener asientos disponibles para un vuelo
    """
    queryset = Reservation.objects.all()
    permission_classes = [IsAuthenticated]
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.service = ReservationService()
    
    def get_serializer_class(self):
        """Seleccionar serializer según la acción"""
        if self.action == 'create':
            return ReservationCreateSerializer
        elif self.action == 'retrieve':
            return ReservationDetailSerializer
        return ReservationSerializer
    
    def get_permissions(self):
        """Permisos según la acción"""
        if self.action in ['retrieve', 'confirm', 'cancel', 'process_payment']:
            return [IsReservationOwnerOrAdmin()]
        return [IsAuthenticated()]
    
    def list(self, request):
        """Listar reservas (admin: todas, usuario: propias)"""
        try:
            if request.user.is_staff:
                # Admin ve todas las reservas
                reservations = Reservation.objects.all().order_by('-reservation_date')
            else:
                # Usuario ve solo sus reservas
                from services.passenger import PassengerService
                passenger_service = PassengerService()
                passenger = passenger_service.get_passenger_by_user(request.user)
                
                if not passenger:
                    return Response(
                        {'error': 'Passenger profile not found'},
                        status=status.HTTP_404_NOT_FOUND
                    )
                
                reservations = self.service.get_reservations_by_passenger(passenger.id)
            
            serializer = self.get_serializer(reservations, many=True)
            return Response(serializer.data)
        except Exception as e:
            return Response(
                {'error': str(e)},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )
    
    def retrieve(self, request, pk=None):
        """Obtener detalle de una reserva"""
        try:
            reservation = self.service.get_reservation_by_id(pk)
            if not reservation:
                return Response(
                    {'error': 'Reservation not found'},
                    status=status.HTTP_404_NOT_FOUND
                )
            
            # Verificar permisos
            self.check_object_permissions(request, reservation)
            
            serializer = self.get_serializer(reservation)
            return Response(serializer.data)
        except Exception as e:
            return Response(
                {'error': str(e)},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )
    
    def create(self, request):
        """Crear una nueva reserva"""
        serializer = self.get_serializer(data=request.data)
        if serializer.is_valid():
            try:
                reservation = self.service.create_reservation(
                    flight_id=serializer.validated_data['flight_id'],
                    passenger_id=serializer.validated_data['passenger_id'],
                    seat_id=serializer.validated_data['seat_id'],
                    notes=serializer.validated_data.get('notes', '')
                )
                return Response(
                    ReservationDetailSerializer(reservation).data,
                    status=status.HTTP_201_CREATED
                )
            except ValidationError as e:
                return Response(
                    {'error': str(e)},
                    status=status.HTTP_400_BAD_REQUEST
                )
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
    
    @action(detail=False, methods=['post'])
    def confirm(self, request):
        """
        Confirmar una reserva.
        Body: { "reservation_code": "ABC123" }
        """
        reservation_code = request.data.get('reservation_code')
        
        if not reservation_code:
            return Response(
                {'error': 'reservation_code is required'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        try:
            reservation = self.service.get_reservation_by_code(reservation_code)
            if not reservation:
                return Response(
                    {'error': 'Reservation not found'},
                    status=status.HTTP_404_NOT_FOUND
                )
            
            # Verificar permisos
            self.check_object_permissions(request, reservation)
            
            confirmed_reservation = self.service.confirm_reservation(reservation_code)
            return Response(ReservationDetailSerializer(confirmed_reservation).data)
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
    
    @action(detail=False, methods=['post'])
    def cancel(self, request):
        """
        Cancelar una reserva.
        Body: { "reservation_code": "ABC123", "reason": "...", "comments": "..." }
        """
        reservation_code = request.data.get('reservation_code')
        reason = request.data.get('reason', '')
        comments = request.data.get('comments', '')
        
        if not reservation_code:
            return Response(
                {'error': 'reservation_code is required'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        try:
            reservation = self.service.get_reservation_by_code(reservation_code)
            if not reservation:
                return Response(
                    {'error': 'Reservation not found'},
                    status=status.HTTP_404_NOT_FOUND
                )
            
            # Verificar permisos
            self.check_object_permissions(request, reservation)
            
            cancelled_reservation = self.service.cancel_reservation(
                reservation_code, reason, comments
            )
            return Response(ReservationDetailSerializer(cancelled_reservation).data)
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
    
    @action(detail=False, methods=['post'])
    def process_payment(self, request):
        """
        Procesar pago de una reserva.
        Body: { "reservation_code": "ABC123", "payment_method": "credit_card" }
        """
        reservation_code = request.data.get('reservation_code')
        payment_method = request.data.get('payment_method', 'credit_card')
        
        if not reservation_code:
            return Response(
                {'error': 'reservation_code is required'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        try:
            reservation = self.service.get_reservation_by_code(reservation_code)
            if not reservation:
                return Response(
                    {'error': 'Reservation not found'},
                    status=status.HTTP_404_NOT_FOUND
                )
            
            # Verificar permisos
            self.check_object_permissions(request, reservation)
            
            result = self.service.process_payment(reservation_code, payment_method)
            
            return Response({
                'reservation': ReservationDetailSerializer(result['reservation']).data,
                'ticket': TicketSerializer(result['ticket']).data
            })
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
    def available_seats(self, request):
        """
        Obtener asientos disponibles para un vuelo.
        Query param: flight_id
        """
        flight_id = request.query_params.get('flight_id')
        
        if not flight_id:
            return Response(
                {'error': 'flight_id is required'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        try:
            seats_data = self.service.get_available_seats_for_flight(flight_id)
            
            from api.serializers import FlightSerializer
            
            return Response({
                'flight': FlightSerializer(seats_data['flight']).data,
                'seats_by_row': seats_data['seats_by_row'],
                'total_available': seats_data['total_available']
            })
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


class TicketViewSet(viewsets.ReadOnlyModelViewSet):
    """
    ViewSet para consultar tickets.
    Solo lectura - los tickets se generan automáticamente al pagar.
    
    list: Listar tickets (admin: todos, usuario: propios)
    retrieve: Obtener detalle de un ticket
    by_barcode: Buscar ticket por código de barras
    by_reservation: Buscar ticket por código de reserva
    """
    queryset = Ticket.objects.all()
    serializer_class = TicketSerializer
    permission_classes = [IsAuthenticated]
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.service = TicketService()
    
    def list(self, request):
        """Listar tickets (admin: todos, usuario: propios)"""
        try:
            if request.user.is_staff:
                tickets = Ticket.objects.all().order_by('-issue_date')
            else:
                from services.passenger import PassengerService
                passenger_service = PassengerService()
                passenger = passenger_service.get_passenger_by_user(request.user)
                
                if not passenger:
                    return Response(
                        {'error': 'Passenger profile not found'},
                        status=status.HTTP_404_NOT_FOUND
                    )
                
                tickets = Ticket.objects.filter(
                    reservation__passenger=passenger
                ).order_by('-issue_date')
            
            serializer = self.get_serializer(tickets, many=True)
            return Response(serializer.data)
        except Exception as e:
            return Response(
                {'error': str(e)},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )
    
    @action(detail=False, methods=['get'])
    def by_barcode(self, request):
        """
        Buscar ticket por código de barras.
        Query param: barcode
        """
        barcode = request.query_params.get('barcode')
        
        if not barcode:
            return Response(
                {'error': 'barcode is required'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        try:
            ticket = self.service.get_ticket_by_barcode(barcode)
            if not ticket:
                return Response(
                    {'error': 'Ticket not found'},
                    status=status.HTTP_404_NOT_FOUND
                )
            
            serializer = self.get_serializer(ticket)
            return Response(serializer.data)
        except Exception as e:
            return Response(
                {'error': str(e)},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )
    
    @action(detail=False, methods=['get'])
    def by_reservation(self, request):
        """
        Buscar ticket por código de reserva.
        Query param: reservation_code
        """
        reservation_code = request.query_params.get('reservation_code')
        
        if not reservation_code:
            return Response(
                {'error': 'reservation_code is required'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        try:
            ticket = self.service.get_ticket_by_reservation_code(reservation_code)
            if not ticket:
                return Response(
                    {'error': 'Ticket not found for this reservation'},
                    status=status.HTTP_404_NOT_FOUND
                )
            
            serializer = self.get_serializer(ticket)
            return Response(serializer.data)
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
