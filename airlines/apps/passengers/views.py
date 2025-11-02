"""
Views para la gestion de pasajeros.

Este archivo contiene:
- Registro de pasajeros
- Perfil de pasajero
- Edicion de info personal
"""

from django.shortcuts import render, redirect
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.core.exceptions import ValidationError

from services.passenger import PassengerService
from services.reservation import ReservationService
from apps.accounts.forms import PassengerForm

passenger_service = PassengerService()
reservation_service = ReservationService()


def register_passenger(request):
    """
    Vista para registrar nuevos pasajeros.
    Puede usarla cualquiera, logueado o no.
    """
    if request.method == 'POST':
        form = PassengerForm(request.POST)
        if form.is_valid():
            try:
                passenger = passenger_service.create_passenger(form.cleaned_data)
                messages.success(
                    request,
                    f'Passenger {passenger.name} registered successfully.'
                )
                
                if request.user.is_authenticated:
                    return redirect('accounts:profile')
                else:
                    return redirect('accounts:login')
                    
            except ValidationError as e:
                messages.error(request, str(e))
            except Exception:
                messages.error(request, 'Error registering passenger. Please try again.')
        else:
            messages.error(request, 'Please correct the errors in the form.')
    else:
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
        passenger = passenger_service.get_passenger_by_email(request.user.email)
        
        if not passenger:
            messages.warning(request, 'You do not have a passenger profile yet. Please complete your information.')
            return redirect('accounts:complete_profile')
        
        stats = reservation_service.get_passenger_stats(passenger.id)
        upcoming_reservations = reservation_service.get_upcoming_reservations(passenger.id, limit=3)
        recent_history = reservation_service.get_reservation_history(passenger.id, limit=5)
        
        context = {
            'passenger': passenger,
            'total_reservations': stats['total'],
            'active_reservations': stats['confirmed'],
            'completed_reservations': stats['completed'],
            'upcoming_reservations': upcoming_reservations,
            'recent_history': recent_history,
        }
        
        return render(request, 'passengers/profile.html', context)
        
    except Exception as e:
        messages.error(request, 'Error loading profile.')
        return redirect('accounts:home')


@login_required
def edit_passenger(request):
    try:
        passenger = passenger_service.get_passenger_by_email(request.user.email)
        
        if not passenger:
            messages.error(request, 'Passenger profile not found.')
            return redirect('accounts:complete_profile')

        if request.method == 'POST':
            form = PassengerForm(request.POST, instance=passenger)
            if form.is_valid():
                try:
                    passenger_service.update_passenger(passenger.id, form.cleaned_data)
                    messages.success(request, 'Information updated successfully.')
                    return redirect('accounts:profile')
                except ValidationError as e:
                    messages.error(request, str(e))
            else:
                messages.error(request, 'Please correct the errors in the form.')
        else:
            form = PassengerForm(instance=passenger)

        context = {
            'form': form,
            'title': 'Edit Personal Information',
        }
        return render(request, 'passengers/passenger_form.html', context)
        
    except Exception as e:
        messages.error(request, 'Error editing passenger.')
        return redirect('accounts:profile')
