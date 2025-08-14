from django.db import models
from django.utils.translation import gettext_lazy as _
from django.utils import timezone
from django.contrib.auth.models import User

class Passenger(models.Model):
    DOCUMENT_TYPES = [
        ('dni', _('DNI')),
        ('passport', _('Passport')),
        ('cedula', _('ID Card')),
        ('license', _('Driver License')),
    ]

    user = models.OneToOneField(
        User,
        on_delete=models.CASCADE,
        related_name='passenger',
        null=True,
        blank=True
    )
    name = models.CharField(_("Full name"), max_length=100)
    document_type = models.CharField(
        _("Document type"),
        max_length=20,
        choices=DOCUMENT_TYPES,
        default='dni'
    )
    document = models.CharField(_("Document number"), max_length=20, unique=True)
    email = models.EmailField(_("Email"))
    phone = models.CharField(_("Phone"), max_length=20)
    birth_date = models.DateField(_("Birth date"))
    active = models.BooleanField(_("Active"), default=True)

    # ----> Campos de fechas con default
    created_at = models.DateTimeField(_("Created at"), default=timezone.now)
    updated_at = models.DateTimeField(_("Updated at"), default=timezone.now)

    class Meta:
        verbose_name = _("Passenger")
        verbose_name_plural = _("Passengers")
        ordering = ['name']

    def __str__(self):
        return self.name

    @property
    def profile_complete(self):
        """Check if all required profile fields are filled"""
        required_fields = [
            self.name,
            self.document_type,
            self.document,
            self.email,
            self.phone,
            self.birth_date
        ]
        return all(required_fields)

    def save(self, *args, **kwargs):
        """Actualiza updated_at al guardar"""
        self.updated_at = timezone.now()
        super().save(*args, **kwargs)
