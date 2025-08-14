from django.shortcuts import render, get_object_or_404, redirect
from django.core.paginator import Paginator
from django.db.models import Q
from django.utils import timezone
from datetime import datetime
from apps.flights.models import Flight, Airplane, Seat

# Create your views here.

"""
Views para manejar vuelos

Este archivo maneja:
- Lista de vuelos disponibles
- Detalle de un vuelo puntual
- Busqueda y filtrado de vuelos
"""


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
    """
    Vista que muestra el detalle de un vuelo puntual
    """
    from apps.reservations.models import Reservation
    # si no existe el vuelo tira error 404
    flight = get_object_or_404(Flight, id=flight_id)
    
    # agarro todos los asientos del avion del vuelo
    seats = flight.airplane.seats.all().order_by('row', 'column')
    
    # busco los asientos ocupados de este vuelo
    occupied_seats = Reservation.objects.filter(
        flight=flight,
        status__in=['confirmed', 'paid', 'completed']
    ).values_list('seat_id', flat=True)
    
    # armo un dict con asientos separados por fila
    seats_by_row = {}
    for seat in seats:
        if seat.row not in seats_by_row:
            seats_by_row[seat.row] = []
        
        # reviso el estado del asiento
        if seat.id in occupied_seats:
            seat_status = 'occupied'
        elif seat.status == 'maintenance':
            seat_status = 'maintenance'
        else:
            seat_status = 'available'
        
        # lo guardo en la fila correspondiente
        seats_by_row[seat.row].append({
            'seat': seat,
            'status': seat_status,
            'price': float(flight.base_price) * seat.extra_price
        })
    
    # calculo totales de asientos
    total_seats = seats.count()
    available_seats = total_seats - len(occupied_seats)
    seats_by_type = {
        'first_class': seats.filter(seat_type='first_class').count(),
        'business': seats.filter(seat_type='business').count(),
        'economy': seats.filter(seat_type='economy').count(),
    }
    
    # chequeo si el usuario puede reservar
    can_book = (
        request.user.is_authenticated and
        flight.status in ['scheduled', 'boarding'] and
        flight.departure_date > timezone.now() and
        available_seats > 0
    )
    
    context = {
        'flight': flight,
        'seats_by_row': dict(sorted(seats_by_row.items())),
        'total_seats': total_seats,
        'available_seats': available_seats,
        'occupied_seats': len(occupied_seats),
        'seats_by_type': seats_by_type,
        'can_book': can_book,
        'base_price': flight.base_price,
    }
    
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
