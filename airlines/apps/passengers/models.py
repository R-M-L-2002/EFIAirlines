from django.db import models
from django.utils.translation import gettext_lazy as _

# Create your models here.

# modelo del pasajero
class Passenger(models.Model):
    # tipos de documento que puede tener el pasajero
    DOCUMENT_TYPES = [
        ('dni', _('dni')),
        ('passport', _('Passport')),
        ('cedula', _('ID Card')),
        ('license', _('Driver License')),
    ]

    name = models.CharField(_("Full name"), max_length=100)   # nombre completo
    document_type = models.CharField(
        _("Document type"),
        max_length=20,
        choices=DOCUMENT_TYPES,
        default='dni'   # por defecto dni
    )
    document = models.CharField(_("Document number"), max_length=20, unique=True) # numero de documento unico
    email = models.EmailField(_("Email"))                   # email
    phone = models.CharField(_("Phone"), max_length=20)     # telefono
    birth_date = models.DateField(_("Birth date"))          # fecha de nacimiento
    active = models.BooleanField(_("Active"), default=True) # si esta activo o no

    def __str__(self):
        return self.name  # asi mostramos el pasajero con su nombre
