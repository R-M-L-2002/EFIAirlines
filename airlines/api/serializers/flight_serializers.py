"""
Serializers para vuelos, aviones y asientos.
"""
from rest_framework import serializers
from django.core.exceptions import ValidationError as DjangoValidationError

# Los modelos aún son necesarios para ModelSerializer (Meta class)
from apps.flights.models import Flight, Airplane, Seat

# NUEVO: Importar los servicios
from services.flight import AirplaneService, FlightService
# (Asegúrate que la ruta de importación 'apps.flights.services' sea correcta)


class AirplaneSerializer(serializers.ModelSerializer):
    """Serializer para el modelo Airplane"""
    available_seats_count = serializers.IntegerField(source='available_seats', read_only=True)
    
    # NUEVO: Instanciar el servicio
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.airplane_service = AirplaneService()

    class Meta:
        model = Airplane
        fields = [
            'id', 'model', 'registration', 'capacity', 'rows', 'columns',
            'active', 'available_seats_count', 'created_at', 'updated_at'
        ]
        read_only_fields = ['id', 'created_at', 'updated_at']
    
    # ELIMINADO: La validación de capacidad ahora está en el servicio.
    # def validate(self, data): ...

    # NUEVO: Sobrescribir create para usar el servicio
    def create(self, validated_data):
        try:
            return self.airplane_service.create_airplane(validated_data)
        except DjangoValidationError as e:
            raise serializers.ValidationError(e.message_dict)

    # NUEVO: Sobrescribir update para usar el servicio
    def update(self, instance, validated_data):
        try:
            return self.airplane_service.update_airplane(instance.id, validated_data)
        except DjangoValidationError as e:
            raise serializers.ValidationError(e.message_dict)


class SeatSerializer(serializers.ModelSerializer):
    """Serializer para el modelo Seat"""
    type_display = serializers.CharField(source='get_type_display', read_only=True)
    status_display = serializers.CharField(source='get_status_display', read_only=True)
    airplane_model = serializers.CharField(source='airplane.model', read_only=True)
    
    class Meta:
        model = Seat
        fields = [
            'id', 'airplane', 'airplane_model', 'seat_number', 'row', 'column',
            'type', 'type_display', 'status', 'status_display', 'extra_price'
        ]
        read_only_fields = ['id']


class FlightListSerializer(serializers.ModelSerializer):
    """Serializer simplificado para listar vuelos (Solo lectura, no necesita servicio)"""
    airplane_model = serializers.CharField(source='airplane.model', read_only=True)
    status_display = serializers.CharField(source='get_status_display', read_only=True)
    available_seats_count = serializers.IntegerField(source='available_seats', read_only=True)
    
    class Meta:
        model = Flight
        fields = [
            'id', 'flight_number', 'origin', 'destination',
            'departure_date', 'arrival_date', 'duration',
            'status', 'status_display', 'base_price',
            'airplane_model', 'available_seats_count', 'is_active'
        ]


class FlightDetailSerializer(serializers.ModelSerializer):
    """
    Serializer detallado para un vuelo específico.
    Usado para lectura (GET) y actualización (PUT/PATCH).
    """
    airplane = AirplaneSerializer(read_only=True)
    airplane_id = serializers.PrimaryKeyRelatedField(
        # MODIFICADO: Quitamos el queryset que consulta directo a la BD
        # El servicio se encargará de validar que el ID del avión es válido.
        queryset=Airplane.objects.none(), # Opcional: poner none() si solo validas en el servicio
        # queryset=Airplane.objects.all(), # O mantenerlo para validación básica de DRF
        source='airplane',
        write_only=True,
        required=False # Asumimos que no siempre se actualiza el avión
    )
    status_display = serializers.CharField(source='get_status_display', read_only=True)
    available_seats_count = serializers.IntegerField(source='available_seats', read_only=True)
    managed_by_username = serializers.CharField(source='managed_by.username', read_only=True, allow_null=True)

    # NUEVO: Instanciar el servicio
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.flight_service = FlightService()

    class Meta:
        model = Flight
        fields = [
            'id', 'flight_number', 'origin', 'destination',
            'departure_date', 'arrival_date', 'duration',
            'status', 'status_display', 'base_price',
            'airplane', 'airplane_id', 'available_seats_count',
            'is_active', 'managed_by', 'managed_by_username', 'created_at'
        ]
        read_only_fields = ['id', 'duration', 'created_at']
    
    # ELIMINADO: La validación de fechas ahora está en el servicio.
    # def validate(self, data): ...

    # NUEVO: Sobrescribir update para usar el servicio
    def update(self, instance, validated_data):
        try:
            return self.flight_service.update_flight(instance.id, validated_data)
        except DjangoValidationError as e:
            raise serializers.ValidationError(e.message_dict)


class FlightSerializer(serializers.ModelSerializer):
    """
    Serializer estándar para Flight (usado para CREAR).
    """
    airplane_model = serializers.CharField(source='airplane.model', read_only=True)
    status_display = serializers.CharField(source='get_status_display', read_only=True)
    
    # NUEVO: Instanciar el servicio
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.flight_service = FlightService()

    class Meta:
        model = Flight
        fields = [
            'id', 'flight_number', 'origin', 'destination',
            'departure_date', 'arrival_date', 'duration',
            'status', 'status_display', 'base_price',
            'airplane', 'airplane_model', 'is_active',
            'managed_by', 'created_at'
        ]
        read_only_fields = ['id', 'duration', 'created_at']
    
    # ELIMINADO: La validación de fechas ahora está en el servicio.
    # def validate(self, data): ...

    # NUEVO: Sobrescribir create para usar el servicio
    def create(self, validated_data):
        try:
            return self.flight_service.create_flight(validated_data)
        except DjangoValidationError as e:
            raise serializers.ValidationError(e.message_dict)