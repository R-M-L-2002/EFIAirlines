from django.contrib import admin
from django.utils.html import format_html
from django.urls import reverse
from .models import Aircraft, Flight, Seat

@admin.register(Aircraft)
class AircraftAdmin(admin.ModelAdmin):
    list_display = ('model', 'capacity', 'rows', 'columns', 'active')
    search_fields = ('model',)

@admin.register(Flight)
class FlightAdmin(admin.ModelAdmin):
    list_display = (
        'flight_number',
        'origin',
        'destination',
        'departure_date',
        'status',
        'available_seats_count',
        'ver_pasajeros_link'
    )
    list_filter = ('status', 'departure_date')
    search_fields = ('flight_number', 'origin', 'destination')

    def available_seats_count(self, obj):
        """Muestra cantidad de asientos libres para este vuelo"""
        return obj.available_seats
    available_seats_count.short_description = 'Asientos Libres'

    def ver_pasajeros_link(self, obj):
        """Link directo al reporte de pasajeros por vuelo"""
        url = reverse('reports:pasajeros_por_vuelo', args=[obj.pk])
        return format_html('<a href="{}" target="_blank">Ver Pasajeros</a>', url)
    ver_pasajeros_link.short_description = "Reporte Pasajeros"

@admin.register(Seat)
class SeatAdmin(admin.ModelAdmin):
    list_display = ('seat_number', 'aircraft', 'type', 'status')
    list_filter = ('type', 'status')
    search_fields = ('seat_number',)