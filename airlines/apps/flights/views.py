from django.shortcuts import render, get_object_or_404, redirect
from django.core.paginator import Paginator
from django.db.models import Q
from django.utils import timezone
from datetime import datetime
from apps.flights.models import Flight, Airplane, Seat
from apps.flights.forms import AirplaneForm, FlightForm
from django.contrib.auth.decorators import user_passes_test
# Create your views here.

"""
Views para manejar vuelos

Este archivo maneja:
- Lista de vuelos disponibles
- Detalle de un vuelo puntual
- Busqueda y filtrado de vuelos
"""

# Decorador para superusuarios
def superuser_required(view_func):
    return user_passes_test(lambda u: u.is_superuser)(view_func)


@superuser_required
def create_airplane(request):
    if request.method == 'POST':
        form = AirplaneForm(request.POST)
        if form.is_valid():
            form.save()
            return redirect('flights:create_flight')  # redirige a crear vuelo después
    else:
        form = AirplaneForm()
    return render(request, 'flights/create_airplane.html', {'form': form})


@superuser_required
def create_flight(request):
    if request.method == 'POST':
        form = FlightForm(request.POST)
        if form.is_valid():
            form.save()
            return redirect('flights:list')
    else:
        form = FlightForm()
    return render(request, 'flights/create_flight.html', {'form': form})

def flight_list(request):
    """
    Vista que muestra todos los vuelos disponibles con opcion de filtro y busqueda
    """
    # agarro lo que viene en la url como filtro de busqueda
    origin = request.GET.get('origin', '')
    destination = request.GET.get('destination', '')
    date_from = request.GET.get('date_from', '')
    date_to = request.GET.get('date_to', '')
    status = request.GET.get('status', '')
    
    # base de la query, por defecto solo vuelos programados o abordando
    flights = Flight.objects.select_related('airplane').filter(
        status__in=['scheduled', 'boarding']
    )
    
    # filtro por origen
    if origin:
        flights = flights.filter(origin__icontains=origin)
    # filtro por destino
    if destination:
        flights = flights.filter(destination__icontains=destination)
    # filtro por fecha desde
    if date_from:
        try:
            date_from_obj = datetime.strptime(date_from, '%Y-%m-%d').date()
            flights = flights.filter(departure_date__date__gte=date_from_obj)
        except ValueError:
            pass
    # filtro por fecha hasta
    if date_to:
        try:
            date_to_obj = datetime.strptime(date_to, '%Y-%m-%d').date()
            flights = flights.filter(departure_date__date__lte=date_to_obj)
        except ValueError:
            pass
    # filtro por estado del vuelo
    if status:
        flights = flights.filter(status=status)
    
    # ordeno por fecha de salida
    flights = flights.order_by('departure_date')
    
    # paginacion, 10 vuelos por pagina
    paginator = Paginator(flights, 10)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)
    
    # agarro todas las ciudades que hay para mostrar en el filtro
    origin_cities = Flight.objects.values_list('origin', flat=True).distinct().order_by('origin')
    destination_cities = Flight.objects.values_list('destination', flat=True).distinct().order_by('destination')
    
    context = {
        'page_obj': page_obj,
        'origin_cities': origin_cities,
        'destination_cities': destination_cities,
        'filters': {
            'origin': origin,
            'destination': destination,
            'date_from': date_from,
            'date_to': date_to,
            'status': status,
        },
        'flight_statuses': Flight.FLIGHT_STATUS,
        'total_flights': paginator.count,
    }
    
    return render(request, 'flights/list.html', context)


def flight_detail(request, flight_id):
    # primero traemos el vuelo, si no existe tira 404
    flight = get_object_or_404(Flight, id=flight_id)

    # traemos todos los asientos de ese avion
    seats = flight.airplane.seats.all()

    # contamos cuantos asientos hay de cada tipo
    seat_counts = {
        'first_class': seats.filter(type='first').count(),      # asientos first class
        'business_class': seats.filter(type='business').count(),# asientos business
        'economy_class': seats.filter(type='economy').count(),  # asientos economy
    }

    # opcional: tambien podrias contar cuántos estan disponibles
    available_counts = {
        'first_class': seats.filter(type='first', status='available').count(),
        'business_class': seats.filter(type='business', status='available').count(),
        'economy_class': seats.filter(type='economy', status='available').count(),
    }

    # ahora armamos el contexto para la plantilla
    context = {
        'flight': flight,
        'seat_counts': seat_counts,
        'available_counts': available_counts,
        'seats': seats,  # si queres mostrar todos los asientos
    }

    # renderizamos la plantilla 'flights/detail.html'
    return render(request, 'flights/detail.html', context)


def search_flights(request):
    """
    Vista para busqueda avanzada de vuelos
    """
    if request.method == 'POST':
        # agarro lo que mando el usuario
        origin = request.POST.get('origin', '')
        destination = request.POST.get('destination', '')
        departure_date = request.POST.get('departure_date', '')
        
        # armo la url para redirigir con los parametros
        params = []
        if origin:
            params.append(f'origin={origin}')
        if destination:
            params.append(f'destination={destination}')
        if departure_date:
            params.append(f'date_from={departure_date}')
        
        url = '/flights/'
        if params:
            url += '?' + '&'.join(params)
        
        return redirect(url)
    
    # agarro todas las ciudades para el select del buscador
    cities = set()
    for flight in Flight.objects.all():
        cities.add(flight.origin)
        cities.add(flight.destination)
    
    context = {
        'cities': sorted(cities),
        'min_date': timezone.now().date(),
    }
    
    return render(request, 'flights/search.html', context)
