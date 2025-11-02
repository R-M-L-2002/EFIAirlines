"""
Configuracion del Django Admin para la app de reservations

Este archivo configura las interfaces de admin para:
- Reservations
- Tickets
"""
from django.contrib import admin
from django.utils.html import format_html
from django.utils import timezone
from .models import Reservation, Ticket

# inline para mostrar el ticket dentro del admin de la reserva
class TicketInline(admin.StackedInline):
    """
    inline para mostrar ticket dentro del admin de reservation
    """
    model = Ticket
    extra = 0
    readonly_fields = [
        'barcode',
        'issue_date',
        'status'
    ]
    
    def has_add_permission(self, request, obj=None):
        # los tickets se crean automatico, no se puede agregar desde aca
        return False


@admin.register(Reservation)
class ReservationAdmin(admin.ModelAdmin):
    """
    configuracion del admin para el modelo Reservation
    """
    list_display = [
        'reservation_code',
        'passenger',
        'flight_info',
        'seat',
        'status',
        'total_price',
        'reservation_date',
        'expiry_status',
        'has_ticket'
    ]
    list_filter = [
        'status',
        'reservation_date',
        'flight__origin',
        'flight__destination',
        'seat__type'
    ]
    search_fields = [
        'reservation_code',
        'passenger__name',
        'passenger__document',
        'flight__flight_number'
    ]
    readonly_fields = [
        'reservation_code',
        'total_price',
        'reservation_date',
        'expiration_date',
        'expiry_status',
        'can_cancel_display'
    ]
    date_hierarchy = 'reservation_date'
    
    fieldsets = (
        ('Reservation info', {
            'fields': ('reservation_code', 'status', 'total_price')
        }),
        ('Travel details', {
            'fields': ('flight', 'passenger', 'seat')
        }),
        ('Important dates', {
            'fields': ('reservation_date', 'expiration_date')
        }),
        ('Status and actions', {
            'fields': ('expiry_status', 'can_cancel_display'),
            'classes': ('collapse',)
        }),
    )
    
    inlines = [TicketInline]
    
    def flight_info(self, obj):
        # muestra info resumida del vuelo
        return f"{obj.flight.flight_number} ({obj.flight.origin} → {obj.flight.destination})"
    flight_info.short_description = 'Flight'
    
    def expiry_status(self, obj):
        # muestra si la reserva esta vencida o cuanto falta
        if obj.status == 'pending':
            if obj.is_expired:
                return format_html('<span style="color: red; font-weight: bold;">EXPIRED</span>')
            else:
                remaining = obj.expiration_date - timezone.now()
                hours = int(remaining.total_seconds() // 3600)
                return format_html('<span style="color: orange;">Expires in {}h</span>', hours)
        return "N/A"
    expiry_status.short_description = 'Expiry'
    
    def can_cancel_display(self, obj):
        # muestra si se puede cancelar la reserva
        if obj.can_cancel:
            return format_html('<span style="color: green;">✓ Can cancel</span>')
        return format_html('<span style="color: red;">✗ Cannot cancel</span>')
    can_cancel_display.short_description = 'Cancellation'
    
    def has_ticket(self, obj):
        # indica si ya tiene ticket generado
        try:
            ticket = obj.ticket
            return format_html('<span style="color: green;">✓ Ticket: {}...</span>', ticket.barcode[:8])
        except Ticket.DoesNotExist:
            return format_html('<span style="color: red;">✗ No ticket</span>')
    has_ticket.short_description = 'Ticket'
    
    actions = ['confirm_reservations', 'cancel_reservations', 'generate_tickets']
    
    def confirm_reservations(self, request, queryset):
        # confirma las reservas pendientes seleccionadas
        confirmed = 0
        for r in queryset.filter(status='pending'):
            r.status = 'confirmed'  # aca se podria llamar a un metodo de tu modelo para confirmar
            r.save()
            confirmed += 1
        self.message_user(request, f'{confirmed} reservation(s) confirmed')
    confirm_reservations.short_description = 'Confirm pending reservations'
    
    def cancel_reservations(self, request, queryset):
        # cancela las reservas seleccionadas
        canceled = 0
        for r in queryset:
            if r.status in ['pending', 'confirmed', 'paid']:
                r.status = 'cancelled'
                r.save()
                canceled += 1
        self.message_user(request, f'{canceled} reservation(s) cancelled')
    cancel_reservations.short_description = 'Cancel reservations'
    
    def generate_tickets(self, request, queryset):
        # genera tickets para reservas confirmadas que no tengan
        generated = 0
        for r in queryset.filter(status__in=['confirmed', 'paid']):
            if not hasattr(r, 'ticket'):
                Ticket.objects.create(reservation=r)
                generated += 1
        self.message_user(request, f'{generated} ticket(s) generated')
    generate_tickets.short_description = 'Generate missing tickets'


@admin.register(Ticket)
class TicketAdmin(admin.ModelAdmin):
    """
    configuracion del admin para el modelo Ticket
    """
    list_display = [
        'short_barcode',
        'reservation_info',
        'passenger_info',
        'status',
        'issue_date',
        'is_valid_display'
    ]
    list_filter = [
        'status',
        'issue_date',
        'reservation__flight__origin',
        'reservation__flight__destination'
    ]
    search_fields = [
        'barcode',
        'reservation__reservation_code',
        'reservation__passenger__name',
        'reservation__passenger__document'
    ]
    readonly_fields = [
        'barcode',
        'issue_date',
        'is_valid_display'
    ]
    date_hierarchy = 'issue_date'
    
    fieldsets = (
        ('Ticket info', {
            'fields': ('reservation', 'barcode', 'status')
        }),
        ('Dates', {
            'fields': ('issue_date',)
        }),
        ('Validation', {
            'fields': ('is_valid_display',),
            'classes': ('collapse',)
        }),
    )
    
    def short_barcode(self, obj):
        # muestra el codigo de barras corto
        return f"{obj.barcode[:8]}..."
    short_barcode.short_description = 'Code'
    
    def reservation_info(self, obj):
        # muestra info de la reserva asociada
        return f"{obj.reservation.reservation_code} ({obj.reservation.get_status_display()})"
    reservation_info.short_description = 'Reservation'
    
    def passenger_info(self, obj):
        # muestra info del pasajero
        return obj.reservation.passenger.name
    passenger_info.short_description = 'Passenger'
    
    def is_valid_display(self, obj):
        # muestra si el ticket es valido
        if obj.status in ['issued', 'used']:
            return format_html('<span style="color: green; font-weight: bold;">✓ VALID</span>')
        return format_html('<span style="color: red; font-weight: bold;">✗ INVALID</span>')
    is_valid_display.short_description = 'Validity'
    
    actions = ['use_tickets', 'cancel_tickets']
    
    def use_tickets(self, request, queryset):
        # marca los tickets como usados (check-in)
        used = 0
        for t in queryset.filter(status='issued'):
            t.status = 'used'
            t.save()
            used += 1
        self.message_user(request, f'{used} ticket(s) marked as used')
    use_tickets.short_description = 'Mark as used (Check-in)'
    
    def cancel_tickets(self, request, queryset):
        # cancela los tickets seleccionados
        updated = 0
        for t in queryset.filter(status__in=['issued', 'used']):
            t.status = 'cancelled'
            t.save()
            updated += 1
        self.message_user(request, f'{updated} ticket(s) canceled')
    cancel_tickets.short_description = 'Cancel tickets'
