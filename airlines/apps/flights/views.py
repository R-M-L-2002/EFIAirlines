from decimal import Decimal
from django.shortcuts import render, get_object_or_404, redirect
from django.core.paginator import Paginator
from django.utils import timezone
from datetime import datetime
from django.contrib.auth.decorators import user_passes_test
from django.contrib import messages
from django.core.exceptions import ValidationError

from services.flight import FlightService, AirplaneService
from apps.flights.forms import AirplaneForm, FlightForm

flight_service = FlightService()
airplane_service = AirplaneService()


def superuser_required(view_func):
    return user_passes_test(lambda u: u.is_superuser)(view_func)


@superuser_required
def create_airplane(request):
    if request.method == 'POST':
        form = AirplaneForm(request.POST)
        if form.is_valid():
            try:
                airplane = airplane_service.create_airplane(form.cleaned_data)
                messages.success(request, f'Airplane {airplane.model} created successfully with seats.')
                return redirect('flights:create_flight')
            except ValidationError as e:
                messages.error(request, str(e))
        else:
            messages.error(request, 'Please correct the errors in the form.')
    else:
        form = AirplaneForm()
    return render(request, 'flights/create_airplane.html', {'form': form})


def create_seats_for_airplane(airplane):
    """Función legacy mantenida por compatibilidad - ahora usa el servicio"""
    pass  # El servicio se encarga de esto automáticamente


@superuser_required
def create_flight(request):
    if request.method == 'POST':
        form = FlightForm(request.POST)
        if form.is_valid():
            try:
                flight = flight_service.create_flight(form.cleaned_data)
                messages.success(request, f'Flight {flight.flight_number} created successfully.')
                return redirect('flights:list')
            except ValidationError as e:
                messages.error(request, str(e))
        else:
            messages.error(request, 'Please correct the errors in the form.')
    else:
        form = FlightForm()
    return render(request, 'flights/create_flight.html', {'form': form})


def flight_list(request):
    filters = {
        'origin': request.GET.get('origin', ''),
        'destination': request.GET.get('destination', ''),
        'status': request.GET.get('status', ''),
    }
    
    date_from = request.GET.get('date_from', '')
    date_to = request.GET.get('date_to', '')
    
    if date_from:
        try:
            filters['date_from'] = datetime.strptime(date_from, '%Y-%m-%d').date()
        except ValueError:
            pass
    
    if date_to:
        try:
            filters['date_to'] = datetime.strptime(date_to, '%Y-%m-%d').date()
        except ValueError:
            pass
    
    flights = flight_service.search_flights(filters)
    
    paginator = Paginator(flights, 10)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)

    cities = flight_service.get_available_cities()

    context = {
        'page_obj': page_obj,
        'origin_cities': cities['origins'],
        'destination_cities': cities['destinations'],
        'filters': {
            'origin': filters.get('origin', ''),
            'destination': filters.get('destination', ''),
            'date_from': date_from,
            'date_to': date_to,
            'status': filters.get('status', ''),
        },
        'flight_statuses': [('scheduled', 'Scheduled'), ('boarding', 'Boarding')],
        'total_flights': paginator.count,
    }
    return render(request, 'flights/list.html', context)


def flight_detail(request, flight_id):
    flight = flight_service.get_flight_by_id(flight_id)
    
    if not flight:
        messages.error(request, 'Flight not found.')
        return redirect('flights:list')
    
    seats = flight.airplane.seats.all()

    seat_counts = {
        'first_class': seats.filter(type='first').count(),
        'business_class': seats.filter(type='business').count(),
        'economy_class': seats.filter(type='economy').count(),
    }

    available_counts = {
        'first_class': seats.filter(type='first', status='available').count(),
        'business_class': seats.filter(type='business', status='available').count(),
        'economy_class': seats.filter(type='economy', status='available').count(),
    }

    context = {
        'flight': flight,
        'seat_counts': seat_counts,
        'available_counts': available_counts,
        'seats': seats,
    }
    return render(request, 'flights/detail.html', context)


@superuser_required
def toggle_flight_active(request, flight_id):
    try:
        flight = flight_service.toggle_flight_active(flight_id)
        status = "activado" if flight.is_active else "desactivado"
        messages.success(request, f"Vuelo {flight.flight_number} {status} con exito.")
    except ValidationError as e:
        messages.error(request, str(e))
    
    return redirect('flights:list')


@superuser_required
def edit_flight(request, flight_id):
    flight = flight_service.get_flight_by_id(flight_id)
    
    if not flight:
        messages.error(request, 'Flight not found.')
        return redirect('flights:list')
    
    if request.method == 'POST':
        form = FlightForm(request.POST, instance=flight)
        if form.is_valid():
            try:
                flight = flight_service.update_flight(flight.id, form.cleaned_data)
                messages.success(request, f"Flight {flight.flight_number} updated successfully.")
                return redirect('flights:detail', flight_id=flight.id)
            except ValidationError as e:
                messages.error(request, str(e))
        else:
            messages.error(request, 'Please correct the errors in the form.')
    else:
        form = FlightForm(instance=flight)
    
    return render(request, 'flights/edit_flight.html', {'form': form, 'flight': flight})


@superuser_required
def delete_flight(request, flight_id):
    flight = flight_service.get_flight_by_id(flight_id)
    
    if not flight:
        messages.error(request, 'Flight not found.')
        return redirect('flights:list')
    
    if request.method == 'POST':
        try:
            flight_number = flight.flight_number
            flight_service.delete_flight(flight_id)
            messages.success(request, f"Flight {flight_number} deleted successfully.")
            return redirect('flights:list')
        except ValidationError as e:
            messages.error(request, str(e))
    
    return render(request, 'flights/delete_flight.html', {'flight': flight})


@superuser_required
def airplane_list(request):
    airplanes = airplane_service.get_all_airplanes()
    
    for airplane in airplanes:
        airplane.total_seats = airplane.seats.count()
        airplane.total_flights = airplane.flights.count()
        airplane.active_flights = airplane.flights.filter(is_active=True, status='scheduled').count()
    
    context = {
        'airplanes': airplanes,
        'total_airplanes': airplanes.count(),
        'active_airplanes': airplanes.filter(active=True).count(),
    }
    return render(request, 'flights/airplane_list.html', context)


@superuser_required
def airplane_detail(request, airplane_id):
    try:
        data = airplane_service.get_airplane_with_layout(airplane_id)
        
        flights = data['airplane'].flights.all().order_by('-departure_date')[:10]
        data['flights'] = flights
        
        return render(request, 'flights/airplane_detail.html', data)
        
    except ValidationError as e:
        messages.error(request, str(e))
        return redirect('flights:airplane_list')


@superuser_required
def edit_airplane(request, airplane_id):
    airplane = airplane_service.get_airplane_by_id(airplane_id)
    
    if not airplane:
        messages.error(request, 'Airplane not found.')
        return redirect('flights:airplane_list')
    
    if request.method == 'POST':
        form = AirplaneForm(request.POST, instance=airplane)
        if form.is_valid():
            try:
                old_rows = airplane.rows
                old_columns = airplane.columns
                
                airplane = airplane_service.update_airplane(airplane.id, form.cleaned_data)
                
                if old_rows != airplane.rows or old_columns != airplane.columns:
                    messages.warning(request, "Seat layout has been regenerated. Previous seat reservations may be affected.")
                
                messages.success(request, f"Airplane {airplane.model} updated successfully.")
                return redirect('flights:airplane_detail', airplane_id=airplane.id)
            except ValidationError as e:
                messages.error(request, str(e))
        else:
            messages.error(request, 'Please correct the errors in the form.')
    else:
        form = AirplaneForm(instance=airplane)
    
    context = {
        'form': form,
        'airplane': airplane,
    }
    return render(request, 'flights/edit_airplane.html', context)


@superuser_required
def delete_airplane(request, airplane_id):
    airplane = airplane_service.get_airplane_by_id(airplane_id)
    
    if not airplane:
        messages.error(request, 'Airplane not found.')
        return redirect('flights:airplane_list')
    
    flights_count = airplane.flights.count()
    
    if request.method == 'POST':
        try:
            airplane_model = airplane.model
            airplane_service.delete_airplane(airplane_id)
            messages.success(request, f"Airplane {airplane_model} deleted successfully.")
            return redirect('flights:airplane_list')
        except ValidationError as e:
            messages.error(request, str(e))
    
    context = {
        'airplane': airplane,
        'flights_count': flights_count,
    }
    return render(request, 'flights/delete_airplane.html', context)


@superuser_required
def toggle_airplane_active(request, airplane_id):
    try:
        airplane = airplane_service.toggle_airplane_active(airplane_id)
        status = "activated" if airplane.active else "deactivated"
        messages.success(request, f"Airplane {airplane.model} {status} successfully.")
    except ValidationError as e:
        messages.error(request, str(e))
    
    return redirect('flights:airplane_list')
