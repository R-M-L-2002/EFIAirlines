from django.db import models
from django.utils.translation import gettext_lazy as _
from django.utils import timezone
from django.core.exceptions import ValidationError
from datetime import timedelta
import random
import string

from apps.passengers.models import Passenger
from apps.flights.models import Flight, Seat


class Reservation(models.Model):
    """
    Este modelo conecta al pasajero con su vuelo y asiento
    """
    STATUS_PENDING = 'pending'
    STATUS_CONFIRMED = 'confirmed'
    STATUS_PAID = 'paid'
    STATUS_CANCELLED = 'canceled'
    STATUS_COMPLETED = 'completed'

    STATUS_CHOICES = [
        (STATUS_PENDING, _('Pending')),
        (STATUS_CONFIRMED, _('Confirmed')),
        (STATUS_PAID, _('Paid')),
        (STATUS_CANCELLED, _('Canceled')),
        (STATUS_COMPLETED, _('Completed')),
    ]

    flight = models.ForeignKey(
        Flight,
        on_delete=models.CASCADE,
        related_name='reservations',
        verbose_name=_("Flight")
    )

    passenger = models.ForeignKey(
        Passenger,
        on_delete=models.CASCADE,
        related_name='reservations',
        verbose_name=_("Passenger")
    )

    seat = models.OneToOneField(
        Seat,
        on_delete=models.CASCADE,
        related_name='reservation',
        verbose_name=_("Seat")
    )

    reservation_code = models.CharField(
        _("Reservation code"),
        max_length=10,
        unique=True,
        blank=True
    )

    status = models.CharField(
        _("Status"),
        max_length=20,
        choices=STATUS_CHOICES,
        default=STATUS_PENDING
    )

    total_price = models.DecimalField(_("Total price"), max_digits=10, decimal_places=2)
    reservation_date = models.DateTimeField(_("Reservation date"), auto_now_add=True)
    expiration_date = models.DateTimeField(_("Expiration date"), blank=True)
    notes = models.TextField(_("Notes"), blank=True, null=True)

    payment_method = models.CharField(
        _("Payment Method"),
        max_length=20,
        blank=True,
        null=True
    )
    payment_notes = models.TextField(
        _("Payment Notes"),
        blank=True,
        null=True
    )

    cancellation_reason = models.CharField(
        _("Cancellation Reason"),
        max_length=100,
        blank=True,
        null=True
    )
    cancellation_comments = models.TextField(
        _("Cancellation Comments"),
        blank=True,
        null=True
    )

    class Meta:
        verbose_name = _("Reservation")
        verbose_name_plural = _("Reservations")
        unique_together = [
            ['flight', 'passenger']  # Un pasajero no puede tener más de una reserva por vuelo
        ]
        ordering = ['-reservation_date']

    def clean(self):
        """Validaciones personalizadas antes de guardar"""
        super().clean()
        
        # Validar que el asiento pertenece al avión del vuelo
        if self.seat and self.flight and self.seat.airplane != self.flight.airplane:
            raise ValidationError({
                'seat': _('The selected seat does not belong to the flight airplane.')
            })
        
        # Validar que el asiento no esté en mantenimiento
        if self.seat and self.seat.status == 'maintenance':
            raise ValidationError({
                'seat': _('The selected seat is under maintenance and cannot be reserved.')
            })
        
        # Validar que el vuelo no haya partido
        if self.flight and self.flight.departure_date < timezone.now():
            raise ValidationError({
                'flight': _('Cannot reserve a seat on a flight that has already departed.')
            })
        
        # Validar duplicados: solo reservas activas, ignora canceladas
        if Reservation.objects.filter(
            flight=self.flight,
            passenger=self.passenger
        ).exclude(status=Reservation.STATUS_CANCELLED).exclude(pk=self.pk).exists():
            raise ValidationError('You already have an active reservation for this flight.')

    def save(self, *args, **kwargs):
        if not self.reservation_code:
            self.reservation_code = self.generate_reservation_code()
        if not self.expiration_date:
            self.expiration_date = timezone.now() + timedelta(hours=24)
        
        is_new = self.pk is None
        old_status = None
        if not is_new:
            old_status = Reservation.objects.get(pk=self.pk).status
        
        super().save(*args, **kwargs)
        
        # Actualizar estado del asiento según el estado de la reserva
        if self.status in [self.STATUS_CONFIRMED, self.STATUS_PAID]:
            self.seat.status = 'reserved'
            self.seat.save()
        elif self.status == self.STATUS_COMPLETED:
            self.seat.status = 'occupied'
            self.seat.save()
        elif self.status == self.STATUS_CANCELLED:
            self.seat.status = 'available'
            self.seat.save()

    def generate_reservation_code(self):
        while True:
            code = ''.join(random.choices(string.ascii_uppercase + string.digits, k=6))
            if not Reservation.objects.filter(reservation_code=code).exists():
                return code

    def __str__(self):
        return f"{self.reservation_code} - {self.passenger.name}"

    @property
    def is_expired(self):
        return timezone.now() > self.expiration_date and self.status == self.STATUS_PENDING

    @property
    def can_cancel(self):
        """
        Permite cancelar si está pendiente, confirmado o pagado y no venció el vuelo
        """
        return self.status in [self.STATUS_PENDING, self.STATUS_CONFIRMED, self.STATUS_PAID] and not self.is_expired


class Ticket(models.Model):
    """
    Este modelo representa el ticket electrónico
    Se genera automáticamente cuando la reserva se confirma
    """
    TICKET_ISSUED = 'issued'
    TICKET_USED = 'used'
    TICKET_CANCELLED = 'canceled'
    TICKET_EXPIRED = 'expired'

    TICKET_STATUS = [
        (TICKET_ISSUED, _('Issued')),
        (TICKET_USED, _('Used')),
        (TICKET_CANCELLED, _('Canceled')),
        (TICKET_EXPIRED, _('Expired')),
    ]

    reservation = models.OneToOneField(
        Reservation,
        on_delete=models.CASCADE,
        related_name='ticket',
        verbose_name=_("Reservation")
    )

    barcode = models.CharField(_("Barcode"), max_length=50, unique=True, blank=True)
    status = models.CharField(_("Status"), max_length=20, choices=TICKET_STATUS, default=TICKET_ISSUED)
    issue_date = models.DateTimeField(_("Issue date"), auto_now_add=True)

    class Meta:
        verbose_name = _("Ticket")
        verbose_name_plural = _("Tickets")
        ordering = ['-issue_date']

    def save(self, *args, **kwargs):
        if not self.barcode:
            self.barcode = self.generate_barcode()
        super().save(*args, **kwargs)

    def generate_barcode(self):
        import random
        while True:
            barcode = ''.join([str(random.randint(0, 9)) for _ in range(12)])
            if not Ticket.objects.filter(barcode=barcode).exists():
                return barcode

    def __str__(self):
        return f"Ticket {self.barcode}"
