from django.shortcuts import render, get_object_or_404
from django.contrib.auth.decorators import login_required, user_passes_test
from django.http import HttpResponse, JsonResponse
from django.db.models import Count, Sum, Avg, Q
from django.utils import timezone
from datetime import datetime, timedelta
import csv
import json

# Create your views here.

"""
Vistas para reportes del sistema de aerolinea
"""


from apps.flights.models import Flight, Airplane, Seat
from apps.passengers.models import Passenger
from apps.reservations.models import Reservation, Ticket
from django.contrib.auth.models import User


def is_staff(user):
    """Chequea si el usuario es staff"""
    return user.is_staff


@login_required
@user_passes_test(is_staff)
def reports_dashboard(request):
    """Dashboard principal de reportes con stats generales"""
    
    # stats generales, cuantos vuelos, pasajeros, reservas y usuarios tenemos
    total_flights = Flight.objects.count()
    total_passengers = Passenger.objects.count()
    total_reservations = Reservation.objects.count()
    total_users = User.objects.count()
    
    # cuantas reservas hay por estado
    reservations_by_status = Reservation.objects.values('status').annotate(
        count=Count('id')
    ).order_by('status')
    
    # vuelos mas populares, los que tienen mas reservas
    popular_flights = Flight.objects.annotate(
        total_reservations=Count('reservation')
    ).order_by('-total_reservations')[:5]
    
    # ingresos por mes, ultimos 6 meses
    six_months_ago = timezone.now() - timedelta(days=180)
    monthly_income = Reservation.objects.filter(
        reservation_date__gte=six_months_ago,
        status__in=['confirmed', 'paid']
    ).extra(
        select={'month': "strftime('%%Y-%%m', reservation_date)"}
    ).values('month').annotate(
        total=Sum('price')
    ).order_by('month')
    
    # ocupacion promedio de vuelos
    flight_occupancy = []
    for flight in Flight.objects.all()[:10]:
        total_seats = flight.airplane.capacity
        occupied_seats = Reservation.objects.filter(
            flight=flight,
            status__in=['confirmed', 'paid']
        ).count()
        percent = (occupied_seats / total_seats * 100) if total_seats > 0 else 0
        flight_occupancy.append({
            'flight': flight,
            'occupancy': round(percent, 1)
        })
    
    # pasajeros que vuelan mas seguido
    frequent_passengers = Passenger.objects.annotate(
        total_flights=Count('reservation', filter=Q(reservation__status__in=['confirmed', 'paid']))
    ).order_by('-total_flights')[:5]
    
    context = {
        'total_flights': total_flights,
        'total_passengers': total_passengers,
        'total_reservations': total_reservations,
        'total_users': total_users,
        'reservations_by_status': reservations_by_status,
        'popular_flights': popular_flights,
        'monthly_income': list(monthly_income),
        'flight_occupancy': flight_occupancy,
        'frequent_passengers': frequent_passengers,
    }
    
    # renderizamos el dashboard con toda la data armada
    return render(request, 'reports/dashboard.html', context)


@login_required
@user_passes_test(is_staff)
def flight_passengers_report(request, flight_id):
    """Reporte detallado de pasajeros de un vuelo especifico"""
    
    flight = get_object_or_404(Flight, id=flight_id)
    
    # traemos todas las reservas del vuelo, con pasajero y asiento ya cargados
    reservations = Reservation.objects.filter(flight=flight).select_related(
        'passenger', 'seat'
    ).order_by('seat__number')
    
    # stats del vuelo
    total_reservations = reservations.count()
    confirmed_reservations = reservations.filter(status__in=['confirmed', 'paid']).count()
    total_income = reservations.filter(status__in=['confirmed', 'paid']).aggregate(
        total=Sum('price')
    )['total'] or 0
    
    # distribucion por tipo de asiento
    seat_distribution = reservations.filter(
        status__in=['confirmed', 'paid']
    ).values('seat__type').annotate(
        count=Count('id')
    )
    
    # exportar a csv si piden
    if request.GET.get('export') == 'csv':
        response = HttpResponse(content_type='text/csv')
        response['Content-Disposition'] = f'attachment; filename="passengers_flight_{flight_id}.csv"'
        
        writer = csv.writer(response)
        writer.writerow([
            'Reservation Code', 'Passenger', 'Document', 'Email', 
            'Seat', 'Seat Type', 'Status', 'Price', 'Reservation Date'
        ])
        
        for reservation in reservations:
            writer.writerow([
                reservation.reservation_code,
                reservation.passenger.name,
                f"{reservation.passenger.document_type}: {reservation.passenger.document}",
                reservation.passenger.email,
                reservation.seat.number,
                reservation.seat.get_type_display(),
                reservation.get_status_display(),
                reservation.price,
                reservation.reservation_date.strftime('%d/%m/%Y %H:%M')
            ])
        
        return response
    
    context = {
        'flight': flight,
        'reservations': reservations,
        'total_reservations': total_reservations,
        'confirmed_reservations': confirmed_reservations,
        'total_income': total_income,
        'seat_distribution': seat_distribution,
        'occupancy_percent': round((confirmed_reservations / flight.airplane.capacity * 100), 1) if flight.airplane.capacity > 0 else 0,
    }
    
    # renderizamos la plantilla del reporte
    return render(request, 'reports/flight_passengers.html', context)


@login_required
@user_passes_test(is_staff)
def income_report(request):
    """Reporte detallado de ingresos por periodo"""
    
    # agarramos parametros de filtro
    start_date = request.GET.get('start_date')
    end_date = request.GET.get('end_date')
    
    # si no pasan nada, por defecto ultimo mes
    if not start_date:
        start_date = (timezone.now() - timedelta(days=30)).date()
    else:
        start_date = datetime.strptime(start_date, '%Y-%m-%d').date()
    
    if not end_date:
        end_date = timezone.now().date()
    else:
        end_date = datetime.strptime(end_date, '%Y-%m-%d').date()
    
    # consulta de reservas en el rango
    reservations_period = Reservation.objects.filter(
        reservation_date__date__range=[start_date, end_date],
        status__in=['confirmed', 'paid']
    )
    
    # stats generales
    total_income = reservations_period.aggregate(total=Sum('price'))['total'] or 0
    total_reservations = reservations_period.count()
    average_income = total_income / total_reservations if total_reservations > 0 else 0
    
    # ingresos por dia
    daily_income = reservations_period.extra(
        select={'date': "date(reservation_date)"}
    ).values('date').annotate(
        total=Sum('price'),
        count=Count('id')
    ).order_by('date')
    
    # ingresos por tipo de asiento
    income_by_type = reservations_period.values(
        'seat__type'
    ).annotate(
        total=Sum('price'),
        count=Count('id')
    ).order_by('-total')
    
    context = {
        'start_date': start_date,
        'end_date': end_date,
        'total_income': total_income,
        'total_reservations': total_reservations,
        'average_income': round(average_income, 2),
        'daily_income': list(daily_income),
        'income_by_type': income_by_type,
    }
    
    # renderizamos el reporte de ingresos
    return render(request, 'reports/income.html', context)


@login_required
@user_passes_test(is_staff)
def export_data(request):
    """Vista para exportar distintos tipos de datos"""
    
    export_type = request.GET.get('type', 'reservations')
    format_type = request.GET.get('format', 'csv')
    
    if export_type == 'reservations':
        return export_reservations_csv(request)
    elif export_type == 'passengers':
        return export_passengers_csv(request)
    elif export_type == 'flights':
        return export_flights_csv(request)
    
    return JsonResponse({'error': 'Tipo de exportacion no valido'}, status=400)


def export_reservations_csv(request):
    """Exportar todas las reservas a CSV"""
    response = HttpResponse(content_type='text/csv')
    response['Content-Disposition'] = 'attachment; filename="all_reservations.csv"'
    
    writer = csv.writer(response)
    writer.writerow([
        'Code', 'Flight', 'Passenger', 'Document', 'Seat', 
        'Status', 'Price', 'Reservation Date', 'Origin', 'Destination'
    ])
    
    reservations = Reservation.objects.select_related(
        'flight', 'passenger', 'seat'
    ).all()
    
    for reservation in reservations:
        writer.writerow([
            reservation.reservation_code,
            f"{reservation.flight.origin} - {reservation.flight.destination}",
            reservation.passenger.name,
            f"{reservation.passenger.document_type}: {reservation.passenger.document}",
            reservation.seat.number,
            reservation.get_status_display(),
            reservation.price,
            reservation.reservation_date.strftime('%d/%m/%Y %H:%M'),
            reservation.flight.origin,
            reservation.flight.destination
        ])
    
    return response


def export_passengers_csv(request):
    """Exportar todos los pasajeros a CSV"""
    response = HttpResponse(content_type='text/csv')
    response['Content-Disposition'] = 'attachment; filename="all_passengers.csv"'
    
    writer = csv.writer(response)
    writer.writerow([
        'Name', 'Document', 'Email', 'Phone', 
        'Birthdate', 'Age', 'Total Flights'
    ])
    
    passengers = Passenger.objects.annotate(
        total_flights=Count('reservation', filter=Q(reservation__status__in=['confirmed', 'paid']))
    )
    
    for passenger in passengers:
        writer.writerow([
            passenger.name,
            f"{passenger.document_type}: {passenger.document}",
            passenger.email,
            passenger.phone,
            passenger.birthdate.strftime('%d/%m/%Y'),
            passenger.age,
            passenger.total_flights
        ])
    
    return response


def export_flights_csv(request):
    """Exportar todos los vuelos a CSV"""
    response = HttpResponse(content_type='text/csv')
    response['Content-Disposition'] = 'attachment; filename="all_flights.csv"'
    
    writer = csv.writer(response)
    writer.writerow([
        'Origin', 'Destination', 'Departure Date', 'Arrival Date', 
        'Duration', 'Airplane', 'Capacity', 'Reservations', 'Status', 'Base Price'
    ])
    
    flights = Flight.objects.select_related('airplane').annotate(
        total_reservations=Count('reservation')
    )
    
    for flight in flights:
        writer.writerow([
            flight.origin,
            flight.destination,
            flight.departure_date.strftime('%d/%m/%Y %H:%M'),
            flight.arrival_date.strftime('%d/%m/%Y %H:%M'),
            flight.duration,
            flight.airplane.model,
            flight.airplane.capacity,
            flight.total_reservations,
            flight.get_status_display(),
            flight.base_price
        ])
    
    return response
