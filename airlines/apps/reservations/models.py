from django.db import models
from django.utils.translation import gettext_lazy as _
from django.utils import timezone
from datetime import timedelta
import uuid
import random
import string

from apps.passengers.models import Passenger
from apps.flights.models import Flight, Seat

# Create your models here.

class Reservation(models.Model):
    """
    este modelo conecta al pasajero con su vuelo y asiento
    """
    RESERVATION_STATUS = [
        ('pending', _('Pending')),     # reserva pendiente
        ('confirmed', _('Confirmed')), # reserva confirmada
        ('paid', _('Paid')),           # reserva pagada
        ('cancelled', _('Cancelled')), # reserva cancelada
        ('completed', _('Completed')), # vuelo completado
    ]

    # vuelo al que pertenece la reserva
    flight = models.ForeignKey(
        Flight,
        on_delete=models.CASCADE,
        related_name='reservations',
        verbose_name=_("Flight")
    )

    # pasajero que hizo la reserva
    passenger = models.ForeignKey(
        Passenger,
        on_delete=models.CASCADE,
        related_name='reservations',
        verbose_name=_("Passenger")
    )

    # asiento que eligio el pasajero
    seat = models.ForeignKey(
        Seat,
        on_delete=models.CASCADE,
        related_name='reservations',
        verbose_name=_("Seat")
    )

    # codigo unico para identificar la reserva
    reservation_code = models.CharField(_("Reservation code"), max_length=10, unique=True, blank=True)

    # estado de la reserva (usa los valores de arriba)
    status = models.CharField(
        _("Status"),
        max_length=20,
        choices=RESERVATION_STATUS,
        default='pending'
    )

    # precio total
    total_price = models.DecimalField(_("Total price"), max_digits=10, decimal_places=2)

    # fecha en que se hizo la reserva
    reservation_date = models.DateTimeField(_("Reservation date"), auto_now_add=True)

    # fecha en que expira la reserva si no se paga
    expiration_date = models.DateTimeField(_("Expiration date"), blank=True)

    class Meta:
        verbose_name = _("Reservation")
        verbose_name_plural = _("Reservations")
        unique_together = ['flight', 'seat']  # no puede haber dos reservas con el mismo vuelo y asiento
        ordering = ['-reservation_date']      # ordena de la mas nueva a la mas vieja

    def save(self, *args, **kwargs):
        # si no tiene codigo, genera uno
        if not self.reservation_code:
            self.reservation_code = self.generate_reservation_code()
        # si no tiene fecha de expiracion, le pone 24 horas despues de ahora
        if not self.expiration_date:
            self.expiration_date = timezone.now() + timedelta(hours=24)
        super().save(*args, **kwargs)

    def generate_reservation_code(self):
        # genera un codigo de 6 caracteres unicos (letras y numeros)
        while True:
            code = ''.join(random.choices(string.ascii_uppercase + string.digits, k=6))
            if not Reservation.objects.filter(reservation_code=code).exists():
                return code

    def __str__(self):
        return f"{self.reservation_code} - {self.passenger.first_name}"

    @property
    def is_expired(self):
        # devuelve True si ya paso la fecha de expiracion y sigue pendiente
        return timezone.now() > self.expiration_date and self.status == 'pending'


class Ticket(models.Model):
    """
    este modelo representa el ticket electronico
    se genera automaticamente cuando la reserva se confirma
    """
    TICKET_STATUS = [
        ('issued', _('Issued')),       # emitido
        ('used', _('Used')),           # usado
        ('cancelled', _('Cancelled')), # cancelado
        ('expired', _('Expired')),     # vencido
    ]

    # cada ticket esta vinculado a una sola reserva
    reservation = models.OneToOneField(
        Reservation,
        on_delete=models.CASCADE,
        related_name='ticket',
        verbose_name=_("Reservation")
    )

    # codigo de barras unico
    barcode = models.CharField(_("Barcode"), max_length=50, unique=True, blank=True)

    # estado del ticket
    status = models.CharField(
        _("Status"),
        max_length=20,
        choices=TICKET_STATUS,
        default='issued'
    )

    # fecha en que se emitio
    issue_date = models.DateTimeField(_("Issue date"), auto_now_add=True)

    class Meta:
        verbose_name = _("Ticket")
        verbose_name_plural = _("Tickets")
        ordering = ['-issue_date']  # de mas nuevo a mas viejo

    def save(self, *args, **kwargs):
        # si no tiene codigo de barras, genera uno
        if not self.barcode:
            self.barcode = self.generate_barcode()
        super().save(*args, **kwargs)

    def generate_barcode(self):
        # genera un codigo unico de 12 caracteres usando uuid
        return str(uuid.uuid4()).replace('-', '').upper()[:12]

    def __str__(self):
        return f"Ticket {self.barcode}"
