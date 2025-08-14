"""
Views para la gestion de pasajeros.

Este archivo contiene:
- Registro de pasajeros
- Perfil de pasajero
- Edicion de info personal
"""

from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.db import transaction
from django.utils import timezone

from .models import Passenger
from apps.accounts.forms import PassengerForm

# Create your views here.

def register_passenger(request):
    """
    Vista para registrar nuevos pasajeros.
    Puede usarla cualquiera, logueado o no.
    """
    if request.method == 'POST':
        # Si vienen datos por POST, usamos el form
        form = PassengerForm(request.POST)
        if form.is_valid():
            try:
                # Hacemos todo en transaccion para que sea seguro
                with transaction.atomic():
                    passenger = form.save()  # guardamos el pasajero
                    messages.success(
                        request,
                        f'Passenger {passenger.name} registered successfully.'
                    )
                    
                    # Si el usuario esta logueado, lo llevamos a su perfil
                    if request.user.is_authenticated:
                        return redirect('accounts:profile')
                    else:
                        # Sino lo mandamos al login
                        return redirect('accounts:login')
                        
            except Exception:
                # Si algo sale mal, avisamos
                messages.error(request, 'Error registering passenger. Please try again.')
        else:
            messages.error(request, 'Please correct the errors in the form.')
    else:
        # Si no es POST, mostramos el form vacio o prellenado
        initial_data = {}
        if request.user.is_authenticated:
            initial_data = {
                'name': f"{request.user.first_name} {request.user.last_name}".strip(),
                'email': request.user.email,
            }
        form = PassengerForm(initial=initial_data)
    
    context = {
        'form': form,
        'title': 'Passenger Registration',
    }
    
    return render(request, 'passengers/register.html', context)


@login_required
def passenger_profile(request):
    """
    Vista para mostrar el perfil del pasajero logueado.
    """
    try:
        # Buscamos al pasajero por el email del usuario
        passenger = Passenger.objects.get(email=request.user.email)
    except Passenger.DoesNotExist:
        # Si no existe perfil, avisamos y mandamos a completar
        messages.warning(request, 'You do not have a passenger profile yet. Please complete your information.')
        return redirect('accounts:complete_profile')
    
    # Contamos reservas totales, activas y completadas
    total_reservations = passenger.reservations.count()
    active_reservations = passenger.reservations.filter(
        status__in=['confirmed', 'paid']
    ).count()
    completed_reservations = passenger.reservations.filter(
        status='completed'
    ).count()
    
    # Tomamos las proximas 3 reservas
    upcoming_reservations = passenger.reservations.filter(
        status__in=['confirmed', 'paid'],
        flight__departure_date__gte=timezone.now()
    ).select_related('flight', 'seat').order_by('flight__departure_date')[:3]
    
    # Tomamos las ultimas 5 reservas completadas
    recent_history = passenger.reservations.filter(
        status='completed'
    ).select_related('flight', 'seat').order_by('-reservation_date')[:5]
    
    context = {
        'passenger': passenger,
        'total_reservations': total_reservations,
        'active_reservations': active_reservations,
        'completed_reservations': completed_reservations,
        'upcoming_reservations': upcoming_reservations,
        'recent_history': recent_history,
    }
    
    return render(request, 'passengers/profile.html', context)


@login_required
def edit_passenger(request):
    try:
        passenger = Passenger.objects.get(email=request.user.email)
    except Passenger.DoesNotExist:
        messages.error(request, 'Passenger profile not found.')
        return redirect('accounts:complete_profile')

    if request.method == 'POST':
        form = PassengerForm(request.POST, instance=passenger)
        if form.is_valid():
            form.save()
            messages.success(request, 'Information updated successfully.')
            # redirigimos al perfil
            return redirect('accounts:profile')  
        else:
            messages.error(request, 'Please correct the errors in the form.')
    else:
        form = PassengerForm(instance=passenger)

    context = {
        'form': form,
        'title': 'Edit Personal Information',
    }
    return render(request, 'passengers/passenger_form.html', context)