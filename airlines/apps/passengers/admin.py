"""
Configuracion del Django Admin para la app de pasajeros
"""
from django.contrib import admin
from django.utils.html import format_html
from .models import Passenger  # importamos el modelo desde models.py


@admin.register(Passenger)
class PassengerAdmin(admin.ModelAdmin):
    """
    Configuracion del admin para el modelo Passenger
    """
    list_display = [
        'name',
        'full_document',
        'email',
        'phone',
        'display_age',
        'total_bookings',
        'active',
        'created_at'
    ]
    list_filter = [
        'document_type',
        'active',
        'birth_date'
    ]
    search_fields = [
        'name',
        'document',
        'email',
        'phone'
    ]
    readonly_fields = [
        'display_age',
        'total_bookings',
    ]
    date_hierarchy = 'birth_date'

    fieldsets = (
        ('Personal Info', {
            'fields': ('name', 'birth_date', 'display_age')
        }),
        ('Documentation', {
            'fields': ('document_type', 'document')
        }),
        ('Contact', {
            'fields': ('email', 'phone')
        }),
        ('Status', {
            'fields': ('active',)
        }),
    )

    def full_document(self, obj):
        return f"{obj.get_document_type_display()}: {obj.document}"
    full_document.short_description = 'Document'

    def display_age(self, obj):
        # calculo de edad simple
        from datetime import date
        today = date.today()
        age = today.year - obj.birth_date.year - ((today.month, today.day) < (obj.birth_date.month, obj.birth_date.day))
        return f"{age} years"
    display_age.short_description = 'Age'

    def total_bookings(self, obj):
        return obj.reservations.count() if hasattr(obj, 'reservations') else 0
    total_bookings.short_description = 'Total Bookings'
