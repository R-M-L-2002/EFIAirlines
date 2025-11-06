"""
Serializers para pasajeros.
"""
from rest_framework import serializers
from apps.passengers.models import Passenger
from django.core.exceptions import ValidationError as DjangoValidationError

from services.passenger import PassengerService


class PassengerSerializer(serializers.ModelSerializer):
    """
    Serializer básico para Passenger.
    Usado para lectura (GET) y actualización (PUT/PATCH).
    """
    document_type_display = serializers.CharField(source='get_document_type_display', read_only=True)
    age = serializers.IntegerField(read_only=True)
    profile_complete = serializers.BooleanField(read_only=True)
    username = serializers.CharField(source='user.username', read_only=True, allow_null=True)
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.passenger_service = PassengerService()

    class Meta:
        model = Passenger
        fields = [
            'id', 'user', 'username', 'name', 'document_type',
            'document_type_display', 'document', 'email', 'phone',
            'birth_date', 'age', 'active', 'profile_complete',
            'created_at', 'updated_at'
        ]
        read_only_fields = ['id', 'created_at', 'updated_at']

    def update(self, instance, validated_data):
        try:
            return self.passenger_service.update_passenger(instance.id, validated_data)
        except DjangoValidationError as e:
            raise serializers.ValidationError(e.message_dict)


class PassengerCreateSerializer(serializers.ModelSerializer):
    """Serializer para crear pasajeros"""
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.passenger_service = PassengerService()
    
    class Meta:
        model = Passenger
        fields = [
            'name', 'document_type', 'document', 'email',
            'phone', 'birth_date', 'user'
        ]
        extra_kwargs = {
            'user': {'required': False, 'allow_null': True}
        }
    
    def create(self, validated_data):
        # espera 'user' como un argumento separado
        user = validated_data.pop('user', None) 
        
        # devuelve un dict {'success': ..., 'message': ..., 'passenger': ...}
        result = self.passenger_service.create_passenger(validated_data, user=user)
        
        if not result['success']:
            raise serializers.ValidationError(result['message'])
            
        return result['passenger']


class PassengerDetailSerializer(serializers.ModelSerializer):
    """Serializer detallado con estadísticas de reservas (Solo lectura)"""
    document_type_display = serializers.CharField(source='get_document_type_display', read_only=True)
    age = serializers.IntegerField(read_only=True)
    profile_complete = serializers.BooleanField(read_only=True)
    username = serializers.CharField(source='user.username', read_only=True, allow_null=True)
    total_reservations = serializers.SerializerMethodField()
    active_reservations = serializers.SerializerMethodField()
    
    class Meta:
        model = Passenger
        fields = [
            'id', 'user', 'username', 'name', 'document_type',
            'document_type_display', 'document', 'email', 'phone',
            'birth_date', 'age', 'active', 'profile_complete',
            'total_reservations', 'active_reservations',
            'created_at', 'updated_at'
        ]
        read_only_fields = ['id', 'created_at', 'updated_at']
    
    def get_total_reservations(self, obj):
        return obj.reservations.count()
    
    def get_active_reservations(self, obj):
        return obj.reservations.filter(status__in=['confirmed', 'paid']).count()