"""
Script para poblar la base de datos con datos de prueba
Ejecutar con: python scripts/seed_database.py
"""

import os
import sys
import django

# Configurar la ruta al proyecto
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'airline.settings')
django.setup()

from datetime import datetime, timedelta
from decimal import Decimal
from django.utils import timezone
from django.contrib.auth.models import User
from apps.flights.models import Airplane, Flight, Seat
from apps.passengers.models import Passenger
from apps.reservations.models import Reservation, Ticket

def create_users():
    """Crea usuarios de prueba si no existen"""
    print("👥 Creando usuarios...")
    
    # Superusuario
    admin, created = User.objects.get_or_create(
        username='admin',
        defaults={
            'email': 'admin@airline.com',
            'first_name': 'Admin',
            'last_name': 'Sistema',
            'is_superuser': True,
            'is_staff': True
        }
    )
    if created:
        admin.set_password('admin123')
        admin.save()
        print(f"   ✓ Superusuario creado: admin / admin123")
    else:
        print(f"   ℹ Superusuario ya existe: admin")
    
    # Usuarios normales
    users_data = [
        {'username': 'juan.perez', 'email': 'juan.perez@email.com', 'first_name': 'Juan', 'last_name': 'Pérez'},
        {'username': 'maria.garcia', 'email': 'maria.garcia@email.com', 'first_name': 'María', 'last_name': 'García'},
        {'username': 'carlos.lopez', 'email': 'carlos.lopez@email.com', 'first_name': 'Carlos', 'last_name': 'López'},
        {'username': 'ana.martinez', 'email': 'ana.martinez@email.com', 'first_name': 'Ana', 'last_name': 'Martínez'},
    ]
    
    users = []
    for user_data in users_data:
        user, created = User.objects.get_or_create(
            username=user_data['username'],
            defaults={
                'email': user_data['email'],
                'first_name': user_data['first_name'],
                'last_name': user_data['last_name']
            }
        )
        if created:
            user.set_password('pass123')
            user.save()
            print(f"   ✓ Usuario creado: {user.username} / pass123")
        else:
            print(f"   ℹ Usuario ya existe: {user.username}")
        users.append(user)
    
    print(f"✅ Usuarios listos\n")
    return users, admin

def create_airplanes():
    """Crea aviones con sus asientos si no existen"""
    print("✈️  Creando aviones...")
    
    airplanes_data = [
        {
            'model': 'Boeing 737-800',
            'registration': 'LV-ABC',
            'capacity': 189,
            'rows': 31,
            'columns': 6
        },
        {
            'model': 'Airbus A320',
            'registration': 'LV-DEF',
            'capacity': 180,
            'rows': 30,
            'columns': 6
        },
        {
            'model': 'Boeing 787 Dreamliner',
            'registration': 'LV-GHI',
            'capacity': 242,
            'rows': 40,
            'columns': 6
        }
    ]
    
    airplanes = []
    for airplane_data in airplanes_data:
        airplane, created = Airplane.objects.get_or_create(
            registration=airplane_data['registration'],
            defaults=airplane_data
        )
        if created:
            print(f"   ✓ Avión creado: {airplane.model} ({airplane.registration})")
        else:
            print(f"   ℹ Avión ya existe: {airplane.model} ({airplane.registration})")
        airplanes.append(airplane)
    
    print(f"✅ Aviones listos\n")
    return airplanes

def create_flights(airplanes, admin_user):
    """Crea vuelos de prueba si no existen"""
    print("🛫 Creando vuelos...")
    
    routes = [
        ('Buenos Aires', 'Mendoza', 2.0, 15000),
        ('Buenos Aires', 'Córdoba', 1.5, 12000),
        ('Buenos Aires', 'Bariloche', 2.5, 18000),
        ('Buenos Aires', 'Salta', 2.5, 17000),
        ('Buenos Aires', 'Puerto Iguazú', 2.0, 16000),
        ('Buenos Aires', 'Santiago de Chile', 2.0, 20000),
        ('Buenos Aires', 'Lima', 4.0, 35000),
        ('Buenos Aires', 'São Paulo', 3.0, 25000),
        ('Córdoba', 'Mendoza', 1.0, 10000),
        ('Mendoza', 'Santiago de Chile', 1.0, 12000),
    ]
    
    flights = []
    flight_counter = 1000
    
    for i, (origin, destination, duration_hours, price) in enumerate(routes):
        flight_number = f'AR{flight_counter + i}'
        
        # Verificar si ya existe
        existing_flight = Flight.objects.filter(flight_number=flight_number).first()
        if existing_flight:
            print(f"   ℹ Vuelo ya existe: {flight_number}")
            flights.append(existing_flight)
            continue
        
        departure = timezone.now() + timedelta(days=i+1, hours=8)
        arrival = departure + timedelta(hours=duration_hours)
        
        flight = Flight.objects.create(
            airplane=airplanes[i % len(airplanes)],
            managed_by=admin_user,
            flight_number=flight_number,
            origin=origin,
            destination=destination,
            departure_date=departure,
            arrival_date=arrival,
            status='scheduled',
            base_price=Decimal(str(price)),
            is_active=True
        )
        flights.append(flight)
        print(f"   ✓ Vuelo creado: {flight.flight_number}: {origin} → {destination} (${flight.base_price})")
    
    print(f"✅ Vuelos listos\n")
    return flights

def create_passengers(users):
    """Crea pasajeros asociados a usuarios si no existen"""
    print("🧳 Creando pasajeros...")
    
    passengers_data = [
        {
            'name': 'Juan Pérez',
            'document_type': 'dni',
            'document': '12345678',
            'email': 'juan.perez@email.com',
            'phone': '+54 11 1234-5678',
            'birth_date': datetime(1990, 5, 15).date()
        },
        {
            'name': 'María García',
            'document_type': 'dni',
            'document': '23456789',
            'email': 'maria.garcia@email.com',
            'phone': '+54 11 2345-6789',
            'birth_date': datetime(1985, 8, 22).date()
        },
        {
            'name': 'Carlos López',
            'document_type': 'passport',
            'document': 'AB123456',
            'email': 'carlos.lopez@email.com',
            'phone': '+54 11 3456-7890',
            'birth_date': datetime(1992, 3, 10).date()
        },
        {
            'name': 'Ana Martínez',
            'document_type': 'dni',
            'document': '34567890',
            'email': 'ana.martinez@email.com',
            'phone': '+54 11 4567-8901',
            'birth_date': datetime(1988, 11, 5).date()
        }
    ]
    
    passengers = []
    for i, passenger_data in enumerate(passengers_data):
        user = users[i] if i < len(users) else None
        
        passenger, created = Passenger.objects.get_or_create(
            document=passenger_data['document'],
            defaults={**passenger_data, 'user': user}
        )
        if created:
            user_info = f" (Usuario: {user.username})" if user else ""
            print(f"   ✓ Pasajero creado: {passenger.name}{user_info}")
        else:
            print(f"   ℹ Pasajero ya existe: {passenger.name}")
        passengers.append(passenger)
    
    print(f"✅ Pasajeros listos\n")
    return passengers

def create_reservations(flights, passengers):
    """Crea reservas de prueba si no existen"""
    print("📋 Creando reservas...")
    
    reservations = []
    created_count = 0
    
    for i in range(min(4, len(flights), len(passengers))):
        flight = flights[i]
        passenger = passengers[i]
        
        # Verificar si ya existe una reserva para este pasajero en este vuelo
        existing = Reservation.objects.filter(flight=flight, passenger=passenger).first()
        if existing:
            print(f"   ℹ Reserva ya existe: {existing.reservation_code}")
            reservations.append(existing)
            continue
        
        # Obtener un asiento disponible
        available_seats = flight.airplane.seats.filter(status='available')
        if available_seats.exists():
            seat = available_seats.first()
            total_price = flight.base_price + seat.extra_price
            
            reservation = Reservation.objects.create(
                flight=flight,
                passenger=passenger,
                seat=seat,
                status='confirmed',
                total_price=total_price,
                payment_method='credit_card',
                notes='Reserva de prueba'
            )
            reservations.append(reservation)
            created_count += 1
            print(f"   ✓ Reserva creada: {reservation.reservation_code} - {passenger.name} en {flight.flight_number}")
    
    if created_count > 0:
        print(f"✅ {created_count} reservas nuevas creadas\n")
    else:
        print(f"✅ Reservas ya existían\n")
    
    return reservations

def create_tickets(reservations):
    """Crea tickets para reservas confirmadas si no existen"""
    print("🎫 Creando tickets...")
    
    tickets = []
    created_count = 0
    confirmed_reservations = [r for r in reservations if r.status in ['confirmed', 'paid']]
    
    for reservation in confirmed_reservations:
        # Verificar si ya existe un ticket
        existing = Ticket.objects.filter(reservation=reservation).first()
        if existing:
            print(f"   ℹ Ticket ya existe: {existing.barcode}")
            tickets.append(existing)
            continue
        
        ticket = Ticket.objects.create(
            reservation=reservation,
            status='issued'
        )
        tickets.append(ticket)
        created_count += 1
        print(f"   ✓ Ticket creado: {ticket.barcode}")
    
    if created_count > 0:
        print(f"✅ {created_count} tickets nuevos creados\n")
    else:
        print(f"✅ Tickets ya existían\n")
    
    return tickets

def main():
    """Función principal que ejecuta todo el seed"""
    print("\n" + "="*60)
    print("🌱 AGREGANDO DATOS A LA BASE DE DATOS")
    print("="*60 + "\n")
    
    try:
        users, admin = create_users()
        airplanes = create_airplanes()
        flights = create_flights(airplanes, admin)
        passengers = create_passengers(users)
        reservations = create_reservations(flights, passengers)
        tickets = create_tickets(reservations)
        
        # Resumen final
        print("\n" + "="*60)
        print("✅ PROCESO COMPLETADO")
        print("="*60)
        print(f"\n📊 Estado actual de la base de datos:")
        print(f"   • Usuarios: {User.objects.count()}")
        print(f"   • Aviones: {Airplane.objects.count()}")
        print(f"   • Asientos: {Seat.objects.count()}")
        print(f"   • Vuelos: {Flight.objects.count()}")
        print(f"   • Pasajeros: {Passenger.objects.count()}")
        print(f"   • Reservas: {Reservation.objects.count()}")
        print(f"   • Tickets: {Ticket.objects.count()}")
        
        print(f"\n🔑 Credenciales de acceso:")
        print(f"   Admin: admin / admin123")
        print(f"   Usuarios: juan.perez, maria.garcia, carlos.lopez, ana.martinez")
        print(f"   Password: pass123")
        
        print("\n" + "="*60 + "\n")
        
    except Exception as e:
        print(f"\n❌ Error durante el seed: {str(e)}")
        import traceback
        traceback.print_exc()
        sys.exit(1)

if __name__ == '__main__':
    main()
