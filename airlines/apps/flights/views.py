from decimal import Decimal
from django.shortcuts import render, get_object_or_404, redirect
from django.core.paginator import Paginator
from django.utils import timezone
from datetime import datetime
from apps.flights.models import Flight, Airplane, Seat
from apps.flights.forms import AirplaneForm, FlightForm
from django.contrib.auth.decorators import user_passes_test

# Decorador para superusuarios
def superuser_required(view_func):
    return user_passes_test(lambda u: u.is_superuser)(view_func)

@superuser_required
def create_airplane(request):
    if request.method == 'POST':
        form = AirplaneForm(request.POST)
        if form.is_valid():
            airplane = form.save()
            # Crear automáticamente los asientos con precio según clase
            create_seats_for_airplane(airplane)
            return redirect('flights:create_flight')
    else:
        form = AirplaneForm()
    return render(request, 'flights/create_airplane.html', {'form': form})

def create_seats_for_airplane(airplane):
    """
    Genera automáticamente los asientos de un avión y asigna tipo y precio.
    """
    letters = 'ABCDEFGHIJKLMNOPQRSTUVWXYZ'
    for row in range(1, airplane.rows + 1):
        for col_index in range(airplane.columns):
            if row <= 2:
                seat_type = 'first'
                price = Decimal('100.00')
            elif row <= 5:
                seat_type = 'business'
                price = Decimal('50.00')
            else:
                seat_type = 'economy'
                price = Decimal('0.00')

            Seat.objects.create(
                airplane=airplane,
                seat_number=f"{row}{letters[col_index]}",
                row=row,
                column=letters[col_index],
                type=seat_type,
                status='available',
                extra_price=price
            )

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
    origin = request.GET.get('origin', '')
    destination = request.GET.get('destination', '')
    date_from = request.GET.get('date_from', '')
    date_to = request.GET.get('date_to', '')
    status = request.GET.get('status', '')

    flights = Flight.objects.select_related('airplane').filter(
        status__in=['scheduled', 'boarding']
    )

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

    flights = flights.order_by('departure_date')
    paginator = Paginator(flights, 10)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)

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
    flight = get_object_or_404(Flight, id=flight_id)
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

def search_flights(request):
    if request.method == 'POST':
        origin = request.POST.get('origin', '')
        destination = request.POST.get('destination', '')
        departure_date = request.POST.get('departure_date', '')

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

    cities = set()
    for flight in Flight.objects.all():
        cities.add(flight.origin)
        cities.add(flight.destination)

    context = {
        'cities': sorted(cities),
        'min_date': timezone.now().date(),
    }
    return render(request, 'flights/search.html', context)
