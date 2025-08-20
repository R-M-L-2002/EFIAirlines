from decimal import Decimal
from django.shortcuts import render, get_object_or_404, redirect
from django.core.paginator import Paginator
from django.utils import timezone
from datetime import datetime
from django.contrib.auth.decorators import user_passes_test
from django.contrib import messages

from apps.flights.models import Flight, Airplane, Seat
from apps.flights.forms import AirplaneForm, FlightForm

# decorador para permitir solo superusuarios
def superuser_required(view_func):
    return user_passes_test(lambda u: u.is_superuser)(view_func)

# vista para crear un avion nuevo
@superuser_required
def create_airplane(request):
    if request.method == 'POST':
        form = AirplaneForm(request.POST)
        if form.is_valid():
            # guardamos el avion y creamos los asientos automaticamente
            airplane = form.save()
            create_seats_for_airplane(airplane)
            return redirect('flights:create_flight')
    else:
        form = AirplaneForm()
    return render(request, 'flights/create_airplane.html', {'form': form})

# funcion para crear los asientos del avion segun filas y columnas
def create_seats_for_airplane(airplane):
    # borramos los asientos antiguos por si ya existian
    Seat.objects.filter(airplane=airplane).delete()
    letters = "ABCDEFGHIJKLMNOPQRSTUVWXYZ"
    
    for row in range(1, airplane.rows + 1):
        for col_index in range(airplane.columns):
            if col_index >= len(letters):  # seguridad si hay muchas columnas
                continue
            seat_number = f"{row}{letters[col_index]}"
            
            # asignamos tipo y precio segun la fila
            if row <= 2:
                seat_type = "first"
                price = 300
            elif row <= 5:
                seat_type = "business"
                price = 200
            else:
                seat_type = "economy"
                price = 100

            # creamos el asiento
            Seat.objects.create(
                airplane=airplane,
                seat_number=seat_number,
                row=row,
                column=letters[col_index],
                type=seat_type,
                status='available',
                extra_price=price
            )

# vista para crear un vuelo nuevo
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

# lista de vuelos con filtros y paginacion
def flight_list(request):
    # obtenemos los filtros de la url
    origin = request.GET.get('origin', '')
    destination = request.GET.get('destination', '')
    date_from = request.GET.get('date_from', '')
    date_to = request.GET.get('date_to', '')
    status = request.GET.get('status', '')

    # solo vuelos activos y con estado programado o embarcando
    flights = Flight.objects.select_related('airplane').filter(
        status__in=['scheduled', 'boarding'],
        is_active=True
    )

    # aplicamos filtros si el usuario eligio alguno
    if origin:
        flights = flights.filter(origin__icontains=origin)
    if destination:
        flights = flights.filter(destination__icontains=destination)
    if date_from:
        try:
            date_from_obj = datetime.strptime(date_from, '%Y-%m-%d').date()
            flights = flights.filter(departure_date__date__gte=date_from_obj)
        except ValueError:
            pass
    if date_to:
        try:
            date_to_obj = datetime.strptime(date_to, '%Y-%m-%d').date()
            flights = flights.filter(departure_date__date__lte=date_to_obj)
        except ValueError:
            pass
    if status:
        flights = flights.filter(status=status)

    # ordenamos por fecha de salida
    flights = flights.order_by('departure_date')
    paginator = Paginator(flights, 10)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)

    # ciudades para los selects de filtro
    origin_cities = Flight.objects.values_list('origin', flat=True).distinct().order_by('origin')
    destination_cities = Flight.objects.values_list('destination', flat=True).distinct().order_by('destination')

    # armamos el context para el template
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

# detalle del vuelo y asientos
def flight_detail(request, flight_id):
    flight = get_object_or_404(Flight, id=flight_id)
    seats = flight.airplane.seats.all()

    # contamos cantidad total de asientos por clase
    seat_counts = {
        'first_class': seats.filter(type='first').count(),
        'business_class': seats.filter(type='business').count(),
        'economy_class': seats.filter(type='economy').count(),
    }

    # contamos cuantos estan disponibles
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

# vista para activar o desactivar un vuelo
@superuser_required
def toggle_flight_active(request, flight_id):
    flight = get_object_or_404(Flight, id=flight_id)
    # cambiamos el estado activo
    flight.is_active = not flight.is_active
    flight.save()
    status = "activado" if flight.is_active else "desactivado"
    messages.success(request, f"Vuelo {flight.flight_number} {status} con exito.")
    return redirect('flights:list')
