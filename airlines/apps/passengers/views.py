"""
Vistas para la gestión de pasajeros.

Este archivo contiene:
- Registro de pasajeros
- Perfil de pasajero
- Edición de información personal
"""
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.db import transaction
from django.utils import timezone

from .models import Pasajero
from apps.accounts.forms import PasajeroForm  # Cambiado de core a accounts


def registro_pasajero(request):
    """
    Vista para registro de nuevos pasajeros.
    Puede ser usada por usuarios no autenticados.
    """
    if request.method == 'POST':
        form = PasajeroForm(request.POST)
        if form.is_valid():
            try:
                with transaction.atomic():
                    pasajero = form.save()
                    messages.success(
                        request,
                        f'Pasajero {pasajero.nombre} registrado exitosamente.'
                    )
                    
                    # Si el usuario está autenticado, redirigir al perfil
                    if request.user.is_authenticated:
                        return redirect('accounts:perfil')  # Cambiado de core a accounts
                    else:
                        return redirect('accounts:login')   # Cambiado de core a accounts
                        
            except Exception as e:
                messages.error(request, 'Error al registrar el pasajero. Intenta nuevamente.')
        else:
            messages.error(request, 'Por favor corrige los errores en el formulario.')
    else:
        # Pre-llenar con datos del usuario si está autenticado
        initial_data = {}
        if request.user.is_authenticated:
            initial_data = {
                'nombre': f"{request.user.first_name} {request.user.last_name}".strip(),
                'email': request.user.email,
            }
        form = PasajeroForm(initial=initial_data)
    
    context = {
        'form': form,
        'titulo': 'Registro de Pasajero',
    }
    
    return render(request, 'pasajeros/registro.html', context)


@login_required
def perfil_pasajero(request):
    """
    Vista para mostrar el perfil del pasajero autenticado.
    """
    try:
        pasajero = Pasajero.objects.get(email=request.user.email)
    except Pasajero.DoesNotExist:
        messages.warning(request, 'No tienes un perfil de pasajero. Completa tu información.')
        return redirect('accounts:completar_perfil')  # Cambiado de core a accounts
    
    # Obtener estadísticas del pasajero
    reservas_totales = pasajero.reservas.count()
    reservas_activas = pasajero.reservas.filter(
        estado__in=['confirmada', 'pagada']
    ).count()
    reservas_completadas = pasajero.reservas.filter(
        estado='completada'
    ).count()
    
    # Próximas reservas
    proximas_reservas = pasajero.reservas.filter(
        estado__in=['confirmada', 'pagada'],
        vuelo__fecha_salida__gte=timezone.now()
    ).select_related('vuelo', 'asiento').order_by('vuelo__fecha_salida')[:3]
    
    # Historial reciente
    historial_reciente = pasajero.reservas.filter(
        estado='completada'
    ).select_related('vuelo', 'asiento').order_by('-fecha_reserva')[:5]
    
    context = {
        'pasajero': pasajero,
        'reservas_totales': reservas_totales,
        'reservas_activas': reservas_activas,
        'reservas_completadas': reservas_completadas,
        'proximas_reservas': proximas_reservas,
        'historial_reciente': historial_reciente,
    }
    
    return render(request, 'pasajeros/perfil.html', context)

    
@login_required
def editar_pasajero(request):
    """
    Vista para editar información del pasajero.
    """
    try:
        pasajero = Pasajero.objects.get(email=request.user.email)
    except Pasajero.DoesNotExist:
        messages.error(request, 'No se encontró tu perfil de pasajero.')
        return redirect('accounts:completar_perfil')  # Cambiado de core a accounts
    
    if request.method == 'POST':
        form = PasajeroForm(request.POST, instance=pasajero)
        if form.is_valid():
            try:
                form.save()
                messages.success(request, 'Información actualizada exitosamente.')
                return redirect('pasajeros:perfil')
            except Exception as e:
                messages.error(request, 'Error al actualizar la información.')
        else:
            messages.error(request, 'Por favor corrige los errores en el formulario.')
    else:
        form = PasajeroForm(instance=pasajero)
    
    context = {
        'form': form,
        'pasajero': pasajero,
        'titulo': 'Editar Información Personal',
    }
    
    return render(request, 'pasajeros/editar.html', context)
