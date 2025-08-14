"""
Vistas para la aplicacion core.

Este archivo contiene:
- Vista home
- Vistas de autenticacion (login, registro, logout)
- Vistas de perfil de usuario
"""
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth import login, authenticate, logout
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.contrib.auth.models import User
from django.db import transaction
from django.urls import reverse
from django.http import JsonResponse
from django.utils import timezone

from .forms import UserRegisterForm, LoginForm, UserProfileForm, PassengerForm
from apps.flights.models import Flight
from apps.passengers.models import Passenger
from apps.reservations.models import Reservation


def home(request):
    """
    Vista principal del sitio.
    Muestra informacion general y vuelos destacados.
    """
    # Obtener vuelos proximos (proximos 5)
    upcoming_flights = Flight.objects.filter(
        status='programmed'
    ).order_by('departure_date')[:5]
    
    # Estadisticas generales
    total_flights = Flight.objects.count()
    total_passengers = Passenger.objects.filter(active=True).count()
    total_reservations = Reservation.objects.filter(
        status__in=['confirmed', 'paid']
    ).count()
    
    context = {
        'upcoming_flights': upcoming_flights,
        'total_flights': total_flights,
        'total_passengers': total_passengers,
        'total_reservations': total_reservations,
    }
    
    return render(request, 'accounts/home.html', context)


def user_registration(request):
    """
    Vista de registro de usuario.
    """
    if request.user.is_authenticated:
        messages.info(request, 'You are already logged in.')
        return redirect('core:home')
    
    if request.method == 'POST':
        form = UserRegisterForm(request.POST)
        if form.is_valid():
            try:
                with transaction.atomic():
                    # Crear usuario
                    user = form.save()
                    
                    # Autenticar y loguear
                    username = form.cleaned_data.get('username')
                    password = form.cleaned_data.get('password')
                    user = authenticate(username=username, password=password)
                    
                    if user:
                        login(request, user)
                        messages.success(
                            request, 
                            f'Welcome {user.first_name}! Your account has been created successfully.'
                        )
                        return redirect('core:complete_profile')
                    
            except Exception:
                messages.error(request, 'Error creating account. Please try again.')
        else:
            messages.error(request, 'Please correct the errors in the form.')
    else:
        form = UserRegisterForm()
    
    return render(request, 'registration/register.html', {'form': form})


def user_login(request):
    """
    Vista de inicio de sesion personalizada.
    """
    if request.user.is_authenticated:
        return redirect('core:home')
    
    if request.method == 'POST':
        form = LoginForm(request, data=request.POST)
        if form.is_valid():
            username = form.cleaned_data.get('username')
            password = form.cleaned_data.get('password')
            user = authenticate(username=username, password=password)
            
            if user is not None:
                login(request, user)
                messages.success(request, f'Welcome back, {user.first_name}!')
                
                # Redirigir a la siguiente pagina o al home
                next_page = request.GET.get('next', 'core:home')
                return redirect(next_page)
            else:
                messages.error(request, 'Invalid username or password.')
        else:
            messages.error(request, 'Please correct the errors in the form.')
    else:
        form = LoginForm()
    
    return render(request, 'registration/login.html', {'form': form})


def user_logout(request):
    """
    Vista de cierre de sesion.
    """
    if request.user.is_authenticated:
        name = request.user.first_name or request.user.username
        logout(request)
        messages.success(request, f'Goodbye, {name}!')
    
    return redirect('core:home')


@login_required
def user_profile(request):
    """
    Vista para mostrar y editar el perfil de usuario.
    """
    # Obtener o crear perfil de pasajero
    try:
        passenger = Passenger.objects.get(email=request.user.email)
    except Passenger.DoesNotExist:
        passenger = None
    
    # Obtener reservas del usuario
    reservations = []
    if passenger:
        reservations = passenger.reservations.all().order_by('-reservation_date')[:5]
    
    context = {
        'passenger': passenger,
        'reservations': reservations,
    }
    
    return render(request, 'accounts/profile.html', context)


@login_required
def edit_profile(request):
    """
    Vista para editar el perfil de usuario.
    """
    if request.method == 'POST':
        form = UserProfileForm(request.POST, instance=request.user)
        if form.is_valid():
            form.save()
            messages.success(request, 'Profile updated successfully.')
            return redirect('core:profile')
        else:
            messages.error(request, 'Please correct the errors in the form.')
    else:
        form = UserProfileForm(instance=request.user)
    
    return render(request, 'core/edit_profile.html', {'form': form})


@login_required
def complete_profile(request):
    """
    Completar el perfil de pasajero despues del registro.
    """
    # Verificar si ya existe el perfil de pasajero para este user
    try:
        passenger = Passenger.objects.get(user=request.user)
        messages.info(request, 'You already have a complete passenger profile.')
        return redirect('core:profile')
    except Passenger.DoesNotExist:
        passenger = Passenger(user=request.user)  # <--- clave

    if request.method == 'POST':
        form = PassengerForm(request.POST, instance=passenger)
        if form.is_valid():
            passenger = form.save(commit=False)
            passenger.user = request.user  # asignar el usuario
            passenger.email = request.user.email  # opcional, si quieres forzar email
            passenger.save()
            messages.success(
                request,
                'Passenger profile completed! You can now make reservations.'
            )
            return redirect('core:profile')
        else:
            messages.error(request, 'Please correct the errors in the form.')
    else:
        initial_data = {
            'name': f"{request.user.first_name} {request.user.last_name}".strip(),
            'email': request.user.email,
        }
        form = PassengerForm(instance=passenger, initial=initial_data)

    return render(request, 'accounts/complete_profile.html', {'form': form})


@login_required
def user_dashboard(request):
    """
    Panel personalizado para usuarios logueados.
    """
    try:
        passenger = Passenger.objects.get(email=request.user.email)
    except Passenger.DoesNotExist:
        messages.warning(request, 'Complete your passenger profile to access all features.')
        return redirect('core:complete_profile')
    
    total_reservations = passenger.reservations.count()
    active_reservations = passenger.reservations.filter(
        status__in=['confirmed', 'paid']
    ).count()
    completed_reservations = passenger.reservations.filter(
        status='completed'
    ).count()
    
    upcoming_reservations = passenger.reservations.filter(
        status__in=['confirmed', 'paid'],
        flight__departure_date__gte=timezone.now()
    ).order_by('flight__departure_date')[:3]
    
    recent_history = passenger.reservations.filter(
        status='completed'
    ).order_by('-reservation_date')[:5]
    
    context = {
        'passenger': passenger,
        'total_reservations': total_reservations,
        'active_reservations': active_reservations,
        'completed_reservations': completed_reservations,
        'upcoming_reservations': upcoming_reservations,
        'recent_history': recent_history,
    }
    
    return render(request, 'core/dashboard.html', context)


def check_username_availability(request):
    """
    Vista AJAX para verificar la disponibilidad de un nombre de usuario.
    """
    if request.method == 'GET':
        username = request.GET.get('username', '')
        if username:
            available = not User.objects.filter(username=username).exists()
            return JsonResponse({'available': available})
    
    return JsonResponse({'available': False})
