"""
Serializers para reservas y tickets.
"""
from rest_framework import serializers
from apps.reservations.models import Reservation, Ticket
from django.core.exceptions import ValidationError as DjangoValidationError

from services.reservation import ReservationService

class TicketSerializer(serializers.ModelSerializer):
    """Serializer para Ticket (Solo lectura)"""
    reservation_code = serializers.CharField(source='reservation.reservation_code', read_only=True)
    passenger_name = serializers.CharField(source='reservation.passenger.name', read_only=True)
    flight_number = serializers.CharField(source='reservation.flight.flight_number', read_only=True)
    status_display = serializers.CharField(source='get_status_display', read_only=True)
    
    class Meta:
        model = Ticket
        fields = [
            'id', 'reservation', 'reservation_code', 'passenger_name',
            'flight_number', 'barcode', 'status', 'status_display', 'issue_date'
        ]
        read_only_fields = ['id', 'barcode', 'issue_date']


class ReservationSerializer(serializers.ModelSerializer):
    """Serializer básico para Reservation (Solo lectura)"""
    passenger_name = serializers.CharField(source='passenger.name', read_only=True)
    flight_number = serializers.CharField(source='flight.flight_number', read_only=True)
    seat_number = serializers.CharField(source='seat.seat_number', read_only=True)
    status_display = serializers.CharField(source='get_status_display', read_only=True)
    is_expired = serializers.BooleanField(read_only=True)
    can_cancel = serializers.BooleanField(read_only=True)
    
    class Meta:
        model = Reservation
        fields = [
            'id', 'reservation_code', 'flight', 'flight_number',
            'passenger', 'passenger_name', 'seat', 'seat_number',
            'status', 'status_display', 'total_price',
            'reservation_date', 'expiration_date', 'notes',
            'is_expired', 'can_cancel', 'payment_method'
        ]
        read_only_fields = [
            'id', 'reservation_code', 'reservation_date',
            'expiration_date', 'total_price'
        ]


class ReservationCreateSerializer(serializers.Serializer):
    """
    Serializer para crear reservas.
    Este NO es un ModelSerializer, solo valida la entrada.
    """
    flight_id = serializers.IntegerField()
    passenger_id = serializers.IntegerField()
    seat_id = serializers.IntegerField()
    notes = serializers.CharField(required=False, allow_blank=True)
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.reservation_service = ReservationService()

    def create(self, validated_data):
        """
        Llama al servicio de creación de reservas.
        validated_data contendrá: {'flight_id': 1, 'passenger_id': 2, 'seat_id': 3, 'notes': '...'}
        """
        try:
            return self.reservation_service.create_reservation(
                flight_id=validated_data['flight_id'],
                passenger_id=validated_data['passenger_id'],
                seat_id=validated_data['seat_id'],
                notes=validated_data.get('notes', '')
            )
        except DjangoValidationError as e:
            raise serializers.ValidationError(e.message)


class ReservationDetailSerializer(serializers.ModelSerializer):
    """Serializer detallado para Reservation (Solo lectura)"""
    passenger = serializers.SerializerMethodField()
    flight = serializers.SerializerMethodField()
    seat = serializers.SerializerMethodField()
    status_display = serializers.CharField(source='get_status_display', read_only=True)
    is_expired = serializers.BooleanField(read_only=True)
    can_cancel = serializers.BooleanField(read_only=True)
    ticket = TicketSerializer(read_only=True)
    
    class Meta:
        model = Reservation
        fields = [
            'id', 'reservation_code', 'flight', 'passenger', 'seat',
            'status', 'status_display', 'total_price',
            'reservation_date', 'expiration_date', 'notes',
            'payment_method', 'payment_notes',
            'cancellation_reason', 'cancellation_comments',
            'is_expired', 'can_cancel', 'ticket'
        ]
        read_only_fields = ['id', 'reservation_code', 'reservation_date', 'total_price']
    
    def get_passenger(self, obj):
        return {
            'id': obj.passenger.id,
            'name': obj.passenger.name,
            'document': obj.passenger.document,
            'email': obj.passenger.email,
            'phone': obj.passenger.phone
        }
    
    def get_flight(self, obj):
        return {
            'id': obj.flight.id,
            'flight_number': obj.flight.flight_number,
            'origin': obj.flight.origin,
            'destination': obj.flight.destination,
            'departure_date': obj.flight.departure_date,
            'arrival_date': obj.flight.arrival_date,
            'status': obj.flight.status
        }
    
    def get_seat(self, obj):
        return {
            'id': obj.seat.id,
            'seat_number': obj.seat.seat_number,
            'type': obj.seat.type,
            'type_display': obj.seat.get_type_display(),
            'extra_price': obj.seat.extra_price
        }