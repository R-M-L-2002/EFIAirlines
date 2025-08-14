from django.db import models
from django.utils.translation import gettext_lazy as _
from django.utils import timezone
from datetime import timedelta

# Create your models here.

class Airplane(models.Model):
    """
    este modelo representa un avion de la aerolinea
    guarda info basica como modelo, capacidad y distribucion de asientos
    """
    model = models.CharField(_("Airplane model"), max_length=100)   # modelo del avion
    capacity = models.PositiveIntegerField(_("Capacity"))           # cantidad total de asientos
    rows = models.PositiveIntegerField(_("Rows"))                   # cantidad de filas
    columns = models.PositiveIntegerField(_("Columns"))             # cantidad de columnas
    active = models.BooleanField(_("Active"), default=True)         # si el avion esta activo o no
    created_at = models.DateTimeField(_("Created at"), auto_now_add=True) # fecha de creacion
    updated_at = models.DateTimeField(_("Updated at"), auto_now=True)     # ultima modificacion

    class Meta:
        verbose_name = _("Airplane")
        verbose_name_plural = _("Airplane")
        ordering = ['model']  # ordena alfabeticamente por modelo

    def __str__(self):
        return f"{self.model} ({self.capacity} seats)"

    @property
    def available_seats(self):
        # calcula cuantos asientos estan disponibles en tiempo real
        return self.seats.filter(status='available').count()


class Flight(models.Model):
    """
    este modelo representa un vuelo programado
    incluye ruta, horario, estado y precio base
    """
    FLIGHT_STATUS = [
        ('scheduled', _('Scheduled')), # programado
        ('boarding', _('Boarding')),   # embarcando
        ('in_flight', _('In Flight')), # en vuelo
        ('landed', _('Landed')),       # aterrizado
        ('cancelled', _('Cancelled')), # cancelado
        ('delayed', _('Delayed')),     # retrasado
    ]

    Airplane = models.ForeignKey(
        Airplane,
        on_delete=models.CASCADE,
        related_name='flights',
        verbose_name=_("Airplane"),
        default=1
    )
    flight_number = models.CharField(_("Flight number"), max_length=10, unique=True) # numero de vuelo
    origin = models.CharField(_("Origin"), max_length=100)                           # ciudad de origen
    destination = models.CharField(_("Destination"), max_length=100)                 # ciudad de destino
    departure_date = models.DateTimeField(_("Departure date"))                       # fecha y hora de salida
    arrival_date = models.DateTimeField(_("Arrival date"))                           # fecha y hora de llegada
    duration = models.DurationField(_("Flight duration"), null=True, blank=True)     # duracion calculada
    status = models.CharField(
        _("Status"),
        max_length=20,
        choices=FLIGHT_STATUS,
        default='scheduled'
    )
    base_price = models.DecimalField(_("Base price"), max_digits=10, decimal_places=2) # precio base
    created_at = models.DateTimeField(_("Created at"), auto_now_add=True)              # fecha de creacion

    class Meta:
        verbose_name = _("Flight")
        verbose_name_plural = _("Flights")
        ordering = ['-departure_date'] # ordena del mas proximo al mas lejano

    def save(self, *args, **kwargs):
        # calcula automaticamente la duracion del vuelo
        if self.departure_date and self.arrival_date:
            self.duration = self.arrival_date - self.departure_date
        super().save(*args, **kwargs)

    def __str__(self):
        return f"{self.flight_number} - {self.origin} → {self.destination}"

    @property
    def available_seats(self):
        # devuelve la cantidad de asientos libres para este vuelo
        reserved_seats = self.reservations.filter(
            status__in=['confirmed', 'paid']
        ).values_list('seat_id', flat=True)
        return self.Airplane.seats.exclude(id__in=reserved_seats).count()


class Seat(models.Model):
    """
    este modelo representa un asiento especifico en un avion
    guarda su ubicacion, tipo y estado
    """
    SEAT_TYPES = [
        ('first', _('First Class')),     # primera clase
        ('business', _('Business Class')), # clase ejecutiva
        ('economy', _('Economy Class')), # clase economica
    ]

    SEAT_STATUS = [
        ('available', _('Available')),   # disponible
        ('reserved', _('Reserved')),     # reservado
        ('occupied', _('Occupied')),     # ocupado
        ('maintenance', _('Maintenance')), # en mantenimiento
    ]

    Airplane = models.ForeignKey(
        Airplane,
        on_delete=models.CASCADE,
        related_name='seats',
        verbose_name=_("Airplane"),
        default=1 
    )
    seat_number = models.CharField(_("Seat number"), max_length=5)   # numero del asiento (ej. 12A)
    row = models.PositiveIntegerField(_("Row"))                      # numero de fila
    column = models.CharField(_("Column"), max_length=1)             # letra de columna
    type = models.CharField(
        _("Seat type"),
        max_length=20,
        choices=SEAT_TYPES,
        default='economy'
    )
    status = models.CharField(
        _("Status"),
        max_length=20,
        choices=SEAT_STATUS,
        default='available'
    )

    class Meta:
        verbose_name = _("Seat")
        verbose_name_plural = _("Seats")
        unique_together = ['Airplane', 'seat_number'] # no puede repetirse el mismo asiento en el mismo avion
        ordering = ['row', 'column']                  # ordena por fila y columna

    def __str__(self):
        return f"{self.seat_number} ({self.get_type_display()})"
