"""
Configuracion del admin de Django para la app de vuelos

Acá configuramos las interfaces del admin para:
- Airplane
- Flights
- Seats
"""
from django.contrib import admin
from django.utils.html import format_html
from apps.flights.models import Airplane, Flight, Seat


class SeatInline(admin.TabularInline):
    """
    Inline para mostrar los asientos dentro del admin del airplane
    """
    model = Seat
    extra = 0
    readonly_fields = ['seat_number', 'row', 'column']
    fields = ['seat_number', 'row', 'column', 'type', 'status']

    def has_add_permission(self, request, obj=None):
        # no dejamos agregar asientos manualmente
        return False


@admin.register(Airplane)
class AirplaneAdmin(admin.ModelAdmin):
    list_display = [
        'model',
        'capacity',
        'rows',
        'columns',
        'total_seats_created',
        'active',
        'created_at',
        'updated_at',
    ]
    list_filter = ['active', 'created_at', 'model']
    search_fields = ['model']
    readonly_fields = ['created_at', 'updated_at']

    fieldsets = (
        ('Airplane Info', {
            'fields': ('model', 'capacity', 'rows', 'columns', 'active')
        }),
        ('Dates', {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )

    inlines = [SeatInline]

    def total_seats_created(self, obj):
        return obj.seats.count()
    total_seats_created.short_description = 'Seats Created'


@admin.register(Flight)
class FlightAdmin(admin.ModelAdmin):
    list_display = [
        'flight_number',
        'airplane',
        'flight_route',
        'departure_date',
        'arrival_date',
        'formatted_duration',
        'status',
        'base_price',
    ]
    list_filter = [
        'status',
        'origin',
        'destination',
        'departure_date',
        'airplane__model'
    ]
    search_fields = [
        'flight_number',
        'origin',
        'destination',
        'airplane__model'
    ]
    date_hierarchy = 'departure_date'
    readonly_fields = ['duration', 'created_at']

    fieldsets = (
        ('Flight Info', {
            'fields': ('flight_number', 'airplane', 'origin', 'destination')
        }),
        ('Dates and Duration', {
            'fields': ('departure_date', 'arrival_date', 'duration')
        }),
        ('Status and Price', {
            'fields': ('status', 'base_price')
        }),
        ('Extra Info', {
            'fields': ('created_at',),
            'classes': ('collapse',)
        }),
    )

    def flight_route(self, obj):
        return f"{obj.origin} → {obj.destination}"
    flight_route.short_description = 'Route'

    def formatted_duration(self, obj):
        if obj.duration:
            total_seconds = int(obj.duration.total_seconds())
            hours = total_seconds // 3600
            minutes = (total_seconds % 3600) // 60
            return f"{hours}h {minutes}m"
        return "-"
    formatted_duration.short_description = 'Duration'


@admin.register(Seat)
class SeatAdmin(admin.ModelAdmin):
    list_display = [
        'seat_number',
        'airplane',
        'row',
        'column',
        'type',
        'status',
    ]
    list_filter = [
        'type',
        'status',
        'airplane__model',
        'row'
    ]
    search_fields = [
        'seat_number',
        'airplane__model'
    ]
    readonly_fields = []

    fieldsets = (
        ('Seat Info', {
            'fields': ('airplane', 'seat_number', 'row', 'column')
        }),
        ('Classification', {
            'fields': ('type', 'status')
        }),
    )
