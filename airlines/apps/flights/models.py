from django.db import models
from django.utils.translation import gettext_lazy as _
from django.utils import timezone
from datetime import timedelta

# Create your models here.

class Airplane(models.Model):
    model = models.CharField(_("Airplane model"), max_length=100)
    capacity = models.PositiveIntegerField(_("Capacity"))
    rows = models.PositiveIntegerField(_("Rows"))
    columns = models.PositiveIntegerField(_("Columns"))
    active = models.BooleanField(_("Active"), default=True)
    created_at = models.DateTimeField(_("Created at"), auto_now_add=True)
    updated_at = models.DateTimeField(_("Updated at"), auto_now=True)

    class Meta:
        verbose_name = _("Airplane")
        verbose_name_plural = _("Airplanes")
        ordering = ['model']

    def __str__(self):
        return f"{self.model} ({self.capacity} seats)"

    def create_seats(self):
        """
        Genera automáticamente los asientos según filas y columnas
        y asigna tipo de asiento según la fila:
        - First Class: filas 1-2
        - Business Class: filas 3-5
        - Economy Class: resto
        """
        letters = 'ABCDEFGHIJKLMNOPQRSTUVWXYZ'
        for row in range(1, self.rows + 1):
            for col_index in range(self.columns):
                if row <= 2:
                    seat_type = 'first'
                elif row <= 5:
                    seat_type = 'business'
                else:
                    seat_type = 'economy'
                
                Seat.objects.create(
                    airplane=self,
                    seat_number=f"{row}{letters[col_index]}",
                    row=row,
                    column=letters[col_index],
                    type=seat_type,
                    status='available'
                )

    def save(self, *args, **kwargs):
        created = self.pk is None
        super().save(*args, **kwargs)
        if created:
            self.create_seats()

    @property
    def available_seats(self):
        """
        Calcula cuantos asientos estan disponibles en tiempo real.
        """
        return self.seats.filter(status='available').count()


class Flight(models.Model):
    """
    Este modelo representa un vuelo programado.
    Incluye ruta, horarios, estado y precio base.
    """
    FLIGHT_STATUS = [
        ('scheduled', _('Scheduled')),
        ('boarding', _('Boarding')),
        ('in_flight', _('In Flight')),
        ('landed', _('Landed')),
        ('cancelled', _('Cancelled')),
        ('delayed', _('Delayed')),
    ]

    airplane = models.ForeignKey(
        Airplane,
        on_delete=models.CASCADE,
        related_name='flights',
        verbose_name=_("Airplane"),
        default=1
    )
    flight_number = models.CharField(_("Flight number"), max_length=10, unique=True)
    origin = models.CharField(_("Origin"), max_length=100)
    destination = models.CharField(_("Destination"), max_length=100)
    departure_date = models.DateTimeField(_("Departure date"))
    arrival_date = models.DateTimeField(_("Arrival date"))
    duration = models.DurationField(_("Flight duration"), null=True, blank=True)
    status = models.CharField(
        _("Status"),
        max_length=20,
        choices=FLIGHT_STATUS,
        default='scheduled'
    )
    base_price = models.DecimalField(_("Base price"), max_digits=10, decimal_places=2)
    is_active = models.BooleanField(
        _("Active"),
        default=True
    )
    created_at = models.DateTimeField(_("Created at"), auto_now_add=True)

    def save(self, *args, **kwargs):
        if self.departure_date and self.arrival_date:
            self.duration = self.arrival_date - self.departure_date
        super().save(*args, **kwargs)

    class Meta:
        verbose_name = _("Flight")
        verbose_name_plural = _("Flights")
        ordering = ['-departure_date'] # ordena del mas proximo al mas lejano

    def save(self, *args, **kwargs):
        """
        Calcula automaticamente la duracion del vuelo antes de guardar.
        """
        if self.departure_date and self.arrival_date:
            self.duration = self.arrival_date - self.departure_date
        super().save(*args, **kwargs)

    def __str__(self):
        return f"{self.flight_number} - {self.origin} → {self.destination}"

    @property
    def available_seats(self):
        """
        Devuelve la cantidad de asientos libres para este vuelo.
        """
        reserved_seats = self.reservations.filter(
            status__in=['confirmed', 'paid']
        ).values_list('seat_id', flat=True)
        return self.airplane.seats.exclude(id__in=reserved_seats).count()


class Seat(models.Model):
    """
    Este modelo representa un asiento especifico en un avion.
    Guarda su ubicacion, tipo y estado.
    """
    SEAT_TYPES = [
        ('first', _('First Class')),
        ('business', _('Business Class')),
        ('economy', _('Economy Class')),
    ]

    SEAT_STATUS = [
        ('available', _('Available')),
        ('reserved', _('Reserved')),
        ('occupied', _('Occupied')),
        ('maintenance', _('Maintenance')),
    ]

    airplane = models.ForeignKey(
        Airplane,
        on_delete=models.CASCADE,
        related_name='seats',
        verbose_name=_("Airplane"),
        default=1
    )
    seat_number = models.CharField(_("Seat number"), max_length=5)  # ej. 12A
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
    extra_price = models.DecimalField(
        _("Extra price"),
        max_digits=10,
        decimal_places=2,
        default=0.0
    )

    class Meta:
        verbose_name = _("Seat")
        verbose_name_plural = _("Seats")
        unique_together = ['airplane', 'seat_number']  # no puede repetirse el mismo asiento en el mismo avion
        ordering = ['row', 'column']                  # ordena por fila y columna

    def __str__(self):
        return f"{self.seat_number} ({self.get_type_display()})"