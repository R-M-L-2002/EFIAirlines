"""
Modelos para la app accounts.

Esta app utiliza principalmente el modelo User predeterminado de Django
para la autenticación y gestión de usuarios. La información adicional
del usuario se almacena en el modelo Pasajero de la app pasajeros.

Si en el futuro se necesita extender la funcionalidad del usuario,
se pueden agregar modelos personalizados aquí.
"""
from django.contrib.auth.models import User
from django.db import models
from django.db.models.signals import post_save
from django.dispatch import receiver

# Por ahora, esta app no requiere modelos personalizados
# ya que utiliza:
# - django.contrib.auth.models.User para autenticación
# - apps.pasajeros.models.Pasajero para información del pasajero

# Ejemplo de cómo se podría extender en el futuro:
# 
# class PerfilUsuario(models.Model):
#     """
#     Extensión del modelo User para información adicional
#     """
#     user = models.OneToOneField(User, on_delete=models.CASCADE)
#     telefono = models.CharField(max_length=20, blank=True)
#     fecha_registro = models.DateTimeField(auto_now_add=True)
#     ultimo_acceso = models.DateTimeField(auto_now=True)
#     preferencias_notificacion = models.BooleanField(default=True)
#     
#     class Meta:
#         verbose_name = 'Perfil de Usuario'
#         verbose_name_plural = 'Perfiles de Usuario'
#     
#     def __str__(self):
#         return f"Perfil de {self.user.username}"

# @receiver(post_save, sender=User)
# def crear_perfil_usuario(sender, instance, created, **kwargs):
#     """
#     Crear automáticamente un perfil cuando se crea un usuario
#     """
#     if created:
#         PerfilUsuario.objects.create(user=instance)
