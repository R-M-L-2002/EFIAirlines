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

from services.report import ReportService

report_service = ReportService()


def is_staff(user):
    """Chequea si el usuario es staff"""
    return user.is_staff


@login_required
@user_passes_test(is_staff)
def reports_dashboard(request):
    """Dashboard principal de reportes con stats generales"""
    
    stats = report_service.get_dashboard_statistics()
    
    context = {
        'total_flights': stats['total_flights'],
        'total_passengers': stats['total_passengers'],
        'total_reservations': stats['total_reservations'],
        'total_users': stats['total_users'],
        'reservations_by_status': stats['reservations_by_status'],
        'popular_flights': stats['popular_flights'],
        'monthly_income': stats['monthly_income'],
        'flight_occupancy': stats['flight_occupancy'],
        'frequent_passengers': stats['frequent_passengers'],
    }
    
    return render(request, 'reports/dashboard.html', context)


@login_required
@user_passes_test(is_staff)
def flight_passengers_report(request, flight_id):
    """Reporte detallado de pasajeros de un vuelo especifico"""
    
    report_data = report_service.get_flight_passengers_report(flight_id)
    
    if not report_data['success']:
        from django.http import Http404
        raise Http404(report_data['message'])
    
    # Exportar a CSV si se solicita
    if request.GET.get('export') == 'csv':
        response = HttpResponse(content_type='text/csv')
        response['Content-Disposition'] = f'attachment; filename="passengers_flight_{flight_id}.csv"'
        
        writer = csv.writer(response)
        writer.writerow([
            'Reservation Code', 'Passenger', 'Document', 'Email', 
            'Seat', 'Seat Type', 'Status', 'Price', 'Reservation Date'
        ])
        
        for reservation in report_data['reservations']:
            writer.writerow([
                reservation.reservation_code,
                reservation.passenger.name,
                f"{reservation.passenger.document_type}: {reservation.passenger.document}",
                reservation.passenger.email,
                reservation.seat.seat_number,
                reservation.seat.get_type_display(),
                reservation.get_status_display(),
                reservation.total_price,
                reservation.reservation_date.strftime('%d/%m/%Y %H:%M')
            ])
        
        return response
    
    context = {
        'flight': report_data['flight'],
        'reservations': report_data['reservations'],
        'total_reservations': report_data['total_reservations'],
        'confirmed_reservations': report_data['confirmed_reservations'],
        'total_income': report_data['total_income'],
        'seat_distribution': report_data['seat_distribution'],
        'occupancy_percent': report_data['occupancy_percent'],
    }
    
    return render(request, 'reports/passenger_flight.html', context)


@login_required
@user_passes_test(is_staff)
def income_report(request):
    """Reporte detallado de ingresos por periodo"""
    
    # Obtener parámetros de filtro
    start_date = request.GET.get('start_date')
    end_date = request.GET.get('end_date')
    
    # Convertir fechas si existen
    start_date_obj = None
    end_date_obj = None
    
    if start_date:
        start_date_obj = datetime.strptime(start_date, '%Y-%m-%d')
    if end_date:
        end_date_obj = datetime.strptime(end_date, '%Y-%m-%d')
    
    report_data = report_service.get_income_report(
        start_date=start_date_obj,
        end_date=end_date_obj
    )
    
    context = {
        'start_date': report_data['start_date'],
        'end_date': report_data['end_date'],
        'total_income': report_data['total_income'],
        'total_reservations': report_data['total_reservations'],
        'average_income': report_data['average_income'],
        'daily_income': report_data['daily_income'],
        'income_by_type': report_data['income_by_type'],
    }
    
    return render(request, 'reports/income.html', context)


@login_required
@user_passes_test(is_staff)
def export_data(request):
    """Vista para exportar distintos tipos de datos"""
    
    export_type = request.GET.get('type', 'reservations')
    
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
    
    reservations_data = report_service.export_reservations_data()
    
    for data in reservations_data:
        writer.writerow([
            data['code'],
            data['flight'],
            data['passenger'],
            data['document'],
            data['seat'],
            data['status'],
            data['price'],
            data['reservation_date'],
            data['origin'],
            data['destination']
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
    
    passengers_data = report_service.export_passengers_data()
    
    for data in passengers_data:
        writer.writerow([
            data['name'],
            data['document'],
            data['email'],
            data['phone'],
            data['birthdate'],
            data['age'],
            data['total_flights']
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
    
    flights_data = report_service.export_flights_data()
    
    for data in flights_data:
        writer.writerow([
            data['origin'],
            data['destination'],
            data['departure_date'],
            data['arrival_date'],
            data['duration'],
            data['airplane'],
            data['capacity'],
            data['reservations'],
            data['status'],
            data['base_price']
        ])
    
    return response
