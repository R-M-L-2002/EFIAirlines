"""
Configuración del Django Admin para la app de pasajeros.

Este archivo configura la interfaz de administración para:
- Pasajeros
"""
from django.contrib import admin
from django.utils.html import format_html
from django.urls import reverse
from .models import Pasajero


@admin.register(Pasajero)
class PasajeroAdmin(admin.ModelAdmin):
    """
    Configuración del admin para el modelo Pasajero.
    """
    list_display = [
        'nombre',
        'documento_completo',
        'email',
        'telefono',
        'edad_display',
        'total_reservas',
        'activo',
        'fecha_registro'
    ]
    list_filter = [
        'tipo_documento',
        'activo',
        'fecha_registro',
        'fecha_nacimiento'
    ]
    search_fields = [
        'nombre',
        'documento',
        'email',
        'telefono'
    ]
    readonly_fields = [
        'edad_display',
        'fecha_registro',
        'fecha_actualizacion',
        'total_reservas',
        'historial_reservas_display'
    ]
    date_hierarchy = 'fecha_registro'
    
    fieldsets = (
        ('Información Personal', {
            'fields': (
                'nombre',
                'fecha_nacimiento',
                'edad_display'
            )
        }),
        ('Documentación', {
            'fields': (
                'tipo_documento',
                'documento'
            )
        }),
        ('Contacto', {
            'fields': (
                'email',
                'telefono'
            )
        }),
        ('Estado', {
            'fields': (
                'activo',
            )
        }),
        ('Información del Sistema', {
            'fields': (
                'total_reservas',
                'historial_reservas_display',
                'fecha_registro',
                'fecha_actualizacion'
            ),
            'classes': ('collapse',)
        }),
    )
    
    def documento_completo(self, obj):
        """
        Muestra el tipo y número de documento juntos
        """
        return f"{obj.get_tipo_documento_display()}: {obj.documento}"
    documento_completo.short_description = 'Documento'
    
    def edad_display(self, obj):
        """
        Muestra la edad calculada del pasajero
        """
        edad = obj.edad
        if edad is not None:
            if obj.es_menor:
                return format_html(
                    '<span style="color: orange; font-weight: bold;">{} años (Menor)</span>',
                    edad
                )
            else:
                return f"{edad} años"
        return "No calculable"
    edad_display.short_description = 'Edad'
    
    def total_reservas(self, obj):
        """
        Muestra el total de reservas del pasajero
        """
        total = obj.reservas.count()
        confirmadas = obj.reservas.filter(
            estado__in=['confirmada', 'pagada', 'completada']
        ).count()
        
        if total > 0:
            return format_html(
                '<span title="Total: {} | Confirmadas: {}">{} reservas</span>',
                total,
                confirmadas,
                total
            )
        return "Sin reservas"
    total_reservas.short_description = 'Reservas'
    
    def historial_reservas_display(self, obj):
        """
        Muestra un enlace al historial de reservas
        """
        reservas = obj.historial_vuelos[:3]  # Últimas 3 reservas
        if reservas:
            html = "<ul>"
            for reserva in reservas:
                html += f"<li>{reserva.codigo_reserva} - {reserva.vuelo.numero_vuelo} ({reserva.get_estado_display()})</li>"
            html += "</ul>"
            
            if obj.reservas.count() > 3:
                html += f"<small>... y {obj.reservas.count() - 3} más</small>"
            
            return format_html(html)
        return "Sin historial"
    historial_reservas_display.short_description = 'Historial Reciente'
    
    actions = ['activar_pasajeros', 'desactivar_pasajeros', 'enviar_email_promocional']
    
    def activar_pasajeros(self, request, queryset):
        """
        Activa pasajeros seleccionados
        """
        updated = queryset.update(activo=True)
        self.message_user(
            request,
            f'{updated} pasajero(s) activado(s).'
        )
    activar_pasajeros.short_description = 'Activar pasajeros seleccionados'
    
    def desactivar_pasajeros(self, request, queryset):
        """
        Desactiva pasajeros seleccionados
        """
        updated = queryset.update(activo=False)
        self.message_user(
            request,
            f'{updated} pasajero(s) desactivado(s).'
        )
    desactivar_pasajeros.short_description = 'Desactivar pasajeros seleccionados'
    
    def enviar_email_promocional(self, request, queryset):
        """
        Simula envío de email promocional (placeholder para funcionalidad futura)
        """
        count = queryset.filter(activo=True).count()
        self.message_user(
            request,
            f'Email promocional enviado a {count} pasajero(s) activo(s).'
        )
    enviar_email_promocional.short_description = 'Enviar email promocional'
