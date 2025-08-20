from django.db import models
from django.utils.translation import gettext_lazy as _
from django.utils import timezone
from datetime import timedelta
import uuid
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
    STATUS_CANCELLED = 'cancelled'
    STATUS_COMPLETED = 'completed'

    STATUS_CHOICES = [
        (STATUS_PENDING, _('Pending')),
        (STATUS_CONFIRMED, _('Confirmed')),
        (STATUS_PAID, _('Paid')),
        (STATUS_CANCELLED, _('Cancelled')),
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

    seat = models.ForeignKey(
        Seat,
        on_delete=models.CASCADE,
        related_name='reservations',
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

    # <- campos nuevos para pagos
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

    class Meta:
        verbose_name = _("Reservation")
        verbose_name_plural = _("Reservations")
        unique_together = ['flight', 'seat']
        ordering = ['-reservation_date']

    def save(self, *args, **kwargs):
        if not self.reservation_code:
            self.reservation_code = self.generate_reservation_code()
        if not self.expiration_date:
            self.expiration_date = timezone.now() + timedelta(hours=24)
        super().save(*args, **kwargs)

    def generate_reservation_code(self):
        while True:
            code = ''.join(random.choices(string.ascii_uppercase + string.digits, k=6))
            if not Reservation.objects.filter(reservation_code=code).exists():
                return code

    def __str__(self):
        return f"{self.reservation_code} - {self.passenger.first_name}"

    @property
    def is_expired(self):
        return timezone.now() > self.expiration_date and self.status == self.STATUS_PENDING

    @property
    def can_cancel(self):
        """
        Permite cancelar si está confirmado o pagado y no venció el vuelo
        """
        return self.status in [self.STATUS_CONFIRMED, self.STATUS_PAID] and not self.is_expired


class Ticket(models.Model):
    """
    Este modelo representa el ticket electrónico
    Se genera automáticamente cuando la reserva se confirma
    """
    TICKET_ISSUED = 'issued'
    TICKET_USED = 'used'
    TICKET_CANCELLED = 'cancelled'
    TICKET_EXPIRED = 'expired'

    TICKET_STATUS = [
        (TICKET_ISSUED, _('Issued')),
        (TICKET_USED, _('Used')),
        (TICKET_CANCELLED, _('Cancelled')),
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
        return str(uuid.uuid4()).replace('-', '').upper()[:12]

    def __str__(self):
        return f"Ticket {self.barcode}"
