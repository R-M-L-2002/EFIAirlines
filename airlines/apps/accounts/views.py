"""
Views for the core app.

This file contains:
- Home view
- Authentication views (login, register, logout)
- User profile views
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

from .forms import RegistroUsuarioForm, LoginForm, PerfilUsuarioForm, PasajeroForm
from apps.flights.models import Vuelo
from apps.passengers.models import Pasajero
from apps.reservations.models import Reserva


def home(request):
    """
    Main site view.
    Shows general info and featured flights.
    """
    # Get upcoming flights (next 5)
    vuelos_proximos = Vuelo.objects.filter(
        estado='programmed'
    ).order_by('fecha_salida')[:5]
    
    # General stats
    total_vuelos = Vuelo.objects.count()
    total_pasajeros = Pasajero.objects.filter(activo=True).count()
    total_reservas = Reserva.objects.filter(
        estado__in=['confirmed', 'paid']
    ).count()
    
    context = {
        'vuelos_proximos': vuelos_proximos,
        'total_vuelos': total_vuelos,
        'total_pasajeros': total_pasajeros,
        'total_reservas': total_reservas,
    }
    
    return render(request, 'accounts/home.html', context)


def registro_usuario(request):
    """
    User registration view.
    """
    if request.user.is_authenticated:
        messages.info(request, 'You are already logged in.')
        return redirect('core:home')
    
    if request.method == 'POST':
        form = RegistroUsuarioForm(request.POST)
        if form.is_valid():
            try:
                with transaction.atomic():
                    # Create user
                    user = form.save()
                    
                    # Authenticate and log in
                    username = form.cleaned_data.get('username')
                    password = form.cleaned_data.get('password')
                    user = authenticate(username=username, password=password)
                    
                    if user:
                        login(request, user)
                        messages.success(
                            request, 
                            f'Welcome {user.first_name}! Your account has been created successfully.'
                        )
                        return redirect('core:completar_perfil')
                    
            except Exception:
                messages.error(request, 'Error creating account. Please try again.')
        else:
            messages.error(request, 'Please correct the errors in the form.')
    else:
        form = RegistroUsuarioForm()
    
    return render(request, 'registration/registro.html', {'form': form})


def login_usuario(request):
    """
    Custom login view.
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
                
                # Redirect to next page or home
                next_page = request.GET.get('next', 'core:home')
                return redirect(next_page)
            else:
                messages.error(request, 'Invalid username or password.')
        else:
            messages.error(request, 'Please correct the errors in the form.')
    else:
        form = LoginForm()
    
    return render(request, 'registration/login.html', {'form': form})


def logout_usuario(request):
    """
    Logout view.
    """
    if request.user.is_authenticated:
        nombre = request.user.first_name or request.user.username
        logout(request)
        messages.success(request, f'Goodbye, {nombre}!')
    
    return redirect('core:home')


@login_required
def perfil_usuario(request):
    """
    View to display and edit user profile.
    """
    # Get or create passenger profile
    try:
        pasajero = Pasajero.objects.get(email=request.user.email)
    except Pasajero.DoesNotExist:
        pasajero = None
    
    # Get user reservations
    reservas = []
    if pasajero:
        reservas = pasajero.reservas.all().order_by('-fecha_reserva')[:5]
    
    context = {
        'pasajero': pasajero,
        'reservas': reservas,
    }
    
    return render(request, 'accounts/perfil.html', context)


@login_required
def editar_perfil(request):
    """
    Edit user profile view.
    """
    if request.method == 'POST':
        form = PerfilUsuarioForm(request.POST, instance=request.user)
        if form.is_valid():
            form.save()
            messages.success(request, 'Profile updated successfully.')
            return redirect('core:perfil')
        else:
            messages.error(request, 'Please correct the errors in the form.')
    else:
        form = PerfilUsuarioForm(instance=request.user)
    
    return render(request, 'core/editar_perfil.html', {'form': form})


@login_required
def completar_perfil(request):
    """
    Complete passenger profile after registration.
    """
    # Check if passenger profile exists
    try:
        pasajero = Pasajero.objects.get(email=request.user.email)
        messages.info(request, 'You already have a complete passenger profile.')
        return redirect('core:perfil')
    except Pasajero.DoesNotExist:
        pass
    
    if request.method == 'POST':
        form = PasajeroForm(request.POST)
        if form.is_valid():
            try:
                with transaction.atomic():
                    pasajero = form.save(commit=False)
                    pasajero.email = request.user.email
                    if not pasajero.nombre:
                        pasajero.nombre = f"{request.user.first_name} {request.user.last_name}".strip()
                    pasajero.save()
                    
                    messages.success(
                        request, 
                        'Passenger profile completed! You can now make reservations.'
                    )
                    return redirect('core:perfil')
                    
            except Exception:
                messages.error(request, 'Error saving profile. Please try again.')
        else:
            messages.error(request, 'Please correct the errors in the form.')
    else:
        initial_data = {
            'nombre': f"{request.user.first_name} {request.user.last_name}".strip(),
            'email': request.user.email,
        }
        form = PasajeroForm(initial=initial_data)
    
    return render(request, 'accounts/completar_perfil.html', {'form': form})


@login_required
def dashboard_usuario(request):
    """
    Custom dashboard for logged-in users.
    """
    try:
        pasajero = Pasajero.objects.get(email=request.user.email)
    except Pasajero.DoesNotExist:
        messages.warning(request, 'Complete your passenger profile to access all features.')
        return redirect('core:completar_perfil')
    
    total_reservas = pasajero.reservas.count()
    reservas_activas = pasajero.reservas.filter(
        estado__in=['confirmed', 'paid']
    ).count()
    reservas_completadas = pasajero.reservas.filter(
        estado='completed'
    ).count()
    
    proximas_reservas = pasajero.reservas.filter(
        estado__in=['confirmed', 'paid'],
        vuelo__fecha_salida__gte=timezone.now()
    ).order_by('vuelo__fecha_salida')[:3]
    
    historial_reciente = pasajero.reservas.filter(
        estado='completed'
    ).order_by('-fecha_reserva')[:5]
    
    context = {
        'pasajero': pasajero,
        'total_reservas': total_reservas,
        'reservas_activas': reservas_activas,
        'reservas_completadas': reservas_completadas,
        'proximas_reservas': proximas_reservas,
        'historial_reciente': historial_reciente,
    }
    
    return render(request, 'core/dashboard.html', context)


def verificar_disponibilidad_usuario(request):
    """
    AJAX view to check username availability.
    """
    if request.method == 'GET':
        username = request.GET.get('username', '')
        if username:
            disponible = not User.objects.filter(username=username).exists()
            return JsonResponse({'disponible': disponible})
    
    return JsonResponse({'disponible': False})
