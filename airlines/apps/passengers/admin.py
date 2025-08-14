from django.contrib import admin
from django.utils.html import format_html
from .models import Passenger

@admin.register(Passenger)
class PassengerAdmin(admin.ModelAdmin):
    list_display = (
        'name',                 # antes 'nombre'
        'documento_completo',
        'email',
        'phone',                 # antes 'telefono'
        'edad_display',
        'total_reservas',
        'active'                 # antes 'activo'
    )

    list_filter = (
        'document_type',         # antes 'tipo_documento'
        'active',
        'birth_date'             # antes 'fecha_nacimiento'
    )

    search_fields = (
        'name',
        'document',
        'email',
        'phone'
    )

    readonly_fields = (
        'edad_display',
        'total_reservas',
        'historial_reservas_display'
    )

    def documento_completo(self, obj):
        return f"{obj.get_document_type_display()}: {obj.document}"
    documento_completo.short_description = 'Documento'

    def edad_display(self, obj):
        from datetime import date
        if obj.birth_date:
            today = date.today()
            edad = today.year - obj.birth_date.year - (
                (today.month, today.day) < (obj.birth_date.month, obj.birth_date.day)
            )
            return f"{edad} años"
        return "No calculable"
    edad_display.short_description = 'Edad'

    def total_reservas(self, obj):
        return obj.reservations.count()
    total_reservas.short_description = 'Reservas'

    def historial_reservas_display(self, obj):
        reservas = obj.reservations.all()[:3]
        if reservas:
            html = "<ul>"
            for r in reservas:
                html += f"<li>{r.reservation_code} - {r.flight.flight_number} ({r.get_status_display()})</li>"
            html += "</ul>"
            if obj.reservations.count() > 3:
                html += f"<small>... y {obj.reservations.count() - 3} más</small>"
            return format_html(html)
        return "Sin historial"
    historial_reservas_display.short_description = 'Historial reciente'