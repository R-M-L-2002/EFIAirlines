"""
Vistas para el sistema de reservas.

Este archivo contiene:
- Creación de nuevas reservas
- Gestión de reservas existentes
- Confirmación y cancelación
- Generación de boletos
"""

from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.db import transaction
from django.http import JsonResponse
from django.utils import timezone
from django.core.paginator import Paginator
from django.views.decorators.http import require_http_methods
import json

from .models import Reservation, Ticket
from .forms import NewReservationForm, ConfirmReservationForm, CancelReservationForm, SeatSelectionForm
from apps.flights.models import Flight, Seat
from apps.passengers.models import Passenger

# Create your views here.

@login_required
def new_reservation(request, flight_id):
    """
    Vista para crear una reserva nueva.
    Incluye selección de asiento y confirmación.
    """
    # busco el vuelo, si no existe tiro 404
    flight = get_object_or_404(Flight, id=flight_id)
    
    # chequeo que el vuelo esté disponible para reservas
    if flight.status not in ['scheduled', 'boarding']:
        messages.error(request, 'This flight is not available for reservations.')
        return redirect('flights:detail', flight_id=flight.id)
    
    # chequeo que la fecha de salida no haya pasado
    if flight.departure_date <= timezone.now():
        messages.error(request, 'Cannot make reservations for flights that have already departed.')
        return redirect('flights:detail', flight_id=flight.id)
    
    # intento agarrar el pasajero asociado al usuario logueado
    try:
        passenger = Passenger.objects.get(email=request.user.email)
    except Passenger.DoesNotExist:
        messages.warning(request, 'You need to complete your passenger profile before booking.')
        return redirect('accounts:complete_profile')
    
    # veo si ya tiene una reserva para este vuelo
    existing_reservation = Reservation.objects.filter(
        flight=flight,
        passenger=passenger,
        status__in=['pending', 'confirmed', 'paid', 'completed']
    ).first()
    
    if existing_reservation:
        messages.info(request, f'You already have a reservation for this flight: {existing_reservation.reservation_code}')
        return redirect('reservations:detail', reservation_code=existing_reservation.reservation_code)
    
    # agarro los asientos que ya están ocupados
    occupied_seats = Reservation.objects.filter(
        flight=flight,
        status__in=['confirmed', 'paid', 'completed']
    ).values_list('seat_id', flat=True)
    
    # filtro los asientos disponibles, saco los ocupados y los que están en mantenimiento
    available_seats = flight.airplane.seats.exclude(
        id__in=occupied_seats
    ).exclude(status='maintenance').order_by('row', 'column')
    
    if not available_seats.exists():
        messages.error(request, 'No seats are available for this flight.')
        return redirect('flights:detail', flight_id=flight.id)
    
    # organizo los asientos por fila para renderizar el mapa
    seats_by_row = {}
    for seat in available_seats:
        if seat.row not in seats_by_row:
            seats_by_row[seat.row] = []
        
        # calculo el precio según el asiento
        seat_price = float(flight.base_price) * seat.extra_price
        seats_by_row[seat.row].append({
            'seat': seat,
            'price': seat_price,
            'available': seat.id not in occupied_seats
        })
    
    # si viene un POST intento crear la reserva
    if request.method == 'POST':
        selected_seat_id = request.POST.get('selected_seat')
        
        if not selected_seat_id:
            messages.error(request, 'You must select a seat.')
            return render(request, 'reservations/new.html', {
                'flight': flight,
                'passenger': passenger,
                'seats_by_row': dict(sorted(seats_by_row.items())),
                'occupied_seats': list(occupied_seats),
            })
        
        try:
            seat = Seat.objects.get(id=selected_seat_id)
            
            # chequeo rápido otra vez que el asiento siga libre
            if seat.id in occupied_seats:
                messages.error(request, 'The selected seat is no longer available.')
                return redirect('reservations:new', flight_id=flight.id)
            
            # todo dentro de una transacción por si falla algo
            with transaction.atomic():
                # creo la reserva
                reservation = Reservation.objects.create(
                    flight=flight,
                    passenger=passenger,
                    seat=seat,
                    status='pending',
                    notes=request.POST.get('notes', '')
                )
                
                messages.success(
                    request,
                    f'Reservation successfully created. Code: {reservation.reservation_code}'
                )
                # redirijo a la página de confirmación
                return redirect('reservations:confirm', reservation_code=reservation.reservation_code)
                
        except Seat.DoesNotExist:
            messages.error(request, 'Invalid seat.')
        except Exception as e:
            messages.error(request, 'Error creating the reservation. Please try again.')
    
    # contexto para renderizar el template
    context = {
        'flight': flight,
        'passenger': passenger,
        'seats_by_row': dict(sorted(seats_by_row.items())),
        'occupied_seats': list(occupied_seats),
        'total_available': available_seats.count(),
    }
    
    return render(request, 'reservations/new.html', context)
