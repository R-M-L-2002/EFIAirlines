"""
Vistas para la aplicacion accounts.

Este archivo contiene:
- Vista home
- Vistas de autenticacion (login, registro, logout)
- Vistas de perfil de usuario
- Vistas de gestion de usuarios para admins
"""
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth import login, logout
from django.contrib.auth.decorators import login_required, user_passes_test
from django.contrib import messages
from django.contrib.auth.models import User
from django.http import JsonResponse

from services.account import AccountService
from services.passenger import PassengerService
from services.flight import FlightService
from services.reservation import ReservationService

from .forms import UserRegisterForm, LoginForm, UserProfileForm, PassengerForm, UserManagementForm


account_service = AccountService()
passenger_service = PassengerService()
flight_service = FlightService()
reservation_service = ReservationService()


def home(request):
    """
    Vista principal del sitio.
    Muestra informacion general y vuelos destacados.
    """
    upcoming_flights = flight_service.get_upcoming_flights(limit=5)

    from repositories.flight import FlightRepository
    from repositories.passenger import PassengerRepository
    from repositories.reservation import ReservationRepository

    total_flights = FlightRepository.get_all().count()
    total_passengers = PassengerRepository.get_all_active().count()
    total_reservations = ReservationRepository.count_by_status(['confirmed', 'paid'])

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
        return redirect('accounts:home')
    
    if request.method == 'POST':
        form = UserRegisterForm(request.POST)
        if form.is_valid():
            result = account_service.register_user(
                username=form.cleaned_data.get('username'),
                email=form.cleaned_data.get('email'),
                password=form.cleaned_data.get('password1'),
                first_name=form.cleaned_data.get('first_name', ''),
                last_name=form.cleaned_data.get('last_name', '')
            )
            
            if result['success']:
                # Autenticar usuario
                user = account_service.authenticate_user(
                    username=form.cleaned_data.get('username'),
                    password=form.cleaned_data.get('password1')
                )
                
                if user:
                    login(request, user)
                    messages.success(
                        request, 
                        f'Welcome {user.first_name}! Your account has been created successfully.'
                    )
                    return redirect('accounts:home')
            else:
                messages.error(request, result['message'])
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
        return redirect('accounts:home')
    
    if request.method == 'POST':
        form = LoginForm(request, data=request.POST)
        if form.is_valid():
            username = form.cleaned_data.get('username')
            password = form.cleaned_data.get('password')
            
            user = account_service.authenticate_user(username, password)
            
            if user is not None:
                login(request, user)
                messages.success(request, f'Welcome back, {user.first_name}!')
                
                next_page = request.GET.get('next', 'accounts:home')
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
    
    return redirect('accounts:home')


@login_required
def user_profile(request):
    """
    Vista para mostrar y editar el perfil de usuario.
    """
    profile_data = account_service.get_user_profile_data(request.user)
    
    context = {
        'passenger': profile_data['passenger'],
        'reservations': profile_data['reservations'],
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
            result = account_service.update_user_profile(
                request.user,
                first_name=form.cleaned_data.get('first_name'),
                last_name=form.cleaned_data.get('last_name'),
                email=form.cleaned_data.get('email')
            )
            
            if result['success']:
                messages.success(request, result['message'])
                return redirect('accounts:profile')
            else:
                messages.error(request, result['message'])
        else:
            messages.error(request, 'Please correct the errors in the form.')
    else:
        form = UserProfileForm(instance=request.user)
    
    return render(request, 'accounts/edit_profile.html', {'form': form})


@login_required
def complete_profile(request):
    """
    Completar el perfil de pasajero despues del registro.
    """
    existing_passenger = passenger_service.get_passenger_by_user(request.user.id)
    
    if existing_passenger:
        messages.info(request, 'You already have a complete passenger profile.')
        return redirect('accounts:profile')

    if request.method == 'POST':
        form = PassengerForm(request.POST)
        if form.is_valid():
            result = passenger_service.create_passenger(
                form.cleaned_data,
                user=request.user
            )
            
            if result['success']:
                messages.success(request, result['message'])
                return redirect('accounts:profile')
            else:
                messages.error(request, result['message'])
        else:
            messages.error(request, 'Please correct the errors in the form.')
    else:
        initial_data = {
            'name': f"{request.user.first_name} {request.user.last_name}".strip(),
            'email': request.user.email,
        }
        form = PassengerForm(initial=initial_data)

    return render(request, 'accounts/complete_profile.html', {'form': form})


@login_required
def user_dashboard(request):
    """
    Panel personalizado para usuarios logueados.
    """
    dashboard_data = account_service.get_user_dashboard_data(request.user)
    
    if not dashboard_data['has_passenger_profile']:
        messages.warning(request, 'Complete your passenger profile to access all features.')
        return redirect('accounts:complete_profile')
    
    context = {
        'passenger': dashboard_data.get('passenger'),
        'total_reservations': dashboard_data.get('total_reservations', 0),
        'active_reservations': dashboard_data.get('active_reservations', 0),
        'completed_reservations': dashboard_data.get('completed_reservations', 0),
        'upcoming_reservations': dashboard_data.get('upcoming_reservations', []),
        'recent_history': dashboard_data.get('recent_history', []),
    }
    
    return render(request, 'accounts/dashboard.html', context)


def check_username_availability(request):
    """
    Vista AJAX para verificar la disponibilidad de un nombre de usuario.
    """
    if request.method == 'GET':
        username = request.GET.get('username', '')
        if username:
            available = account_service.check_username_availability(username)
            return JsonResponse({'available': available})
    
    return JsonResponse({'available': False})


@login_required
@user_passes_test(lambda u: u.is_superuser)
def manage_users(request):
    """
    Vista para listar todos los usuarios del sistema.
    Solo accesible para superusuarios.
    """
    search = request.GET.get('search', '')
    users = account_service.search_users(search)
    
    context = {
        'users': users,
        'search': search,
    }
    
    return render(request, 'accounts/manage_users.html', context)


@login_required
@user_passes_test(lambda u: u.is_superuser)
def create_user(request):
    """
    Vista para crear un nuevo usuario.
    Solo accesible para superusuarios.
    """
    if request.method == 'POST':
        form = UserManagementForm(request.POST)
        if form.is_valid():
            result = account_service.create_user_admin(
                username=form.cleaned_data.get('username'),
                email=form.cleaned_data.get('email'),
                password=form.cleaned_data.get('password1'),
                first_name=form.cleaned_data.get('first_name', ''),
                last_name=form.cleaned_data.get('last_name', ''),
                is_staff=form.cleaned_data.get('is_staff', False),
                is_superuser=form.cleaned_data.get('is_superuser', False)
            )
            
            if result['success']:
                messages.success(request, result['message'])
                return redirect('accounts:manage_users')
            else:
                messages.error(request, result['message'])
        else:
            messages.error(request, 'Please correct the errors in the form.')
    else:
        form = UserManagementForm()
    
    return render(request, 'accounts/create_user.html', {'form': form})


@login_required
@user_passes_test(lambda u: u.is_superuser)
def edit_user(request, user_id):
    """
    Vista para editar un usuario existente.
    Solo accesible para superusuarios.
    """
    user = get_object_or_404(User, id=user_id)
    
    if request.method == 'POST':
        form = UserManagementForm(request.POST, instance=user)
        if form.is_valid():
            result = account_service.update_user_admin(
                user_id=user_id,
                first_name=form.cleaned_data.get('first_name'),
                last_name=form.cleaned_data.get('last_name'),
                email=form.cleaned_data.get('email'),
                is_staff=form.cleaned_data.get('is_staff', False),
                is_superuser=form.cleaned_data.get('is_superuser', False)
            )
            
            if result['success']:
                messages.success(request, result['message'])
                return redirect('accounts:manage_users')
            else:
                messages.error(request, result['message'])
        else:
            messages.error(request, 'Please correct the errors in the form.')
    else:
        form = UserManagementForm(instance=user)
    
    context = {
        'form': form,
        'user_obj': user,
    }
    
    return render(request, 'accounts/edit_user.html', context)


@login_required
@user_passes_test(lambda u: u.is_superuser)
def delete_user(request, user_id):
    """
    Vista para eliminar un usuario.
    Solo accesible para superusuarios.
    """
    user = get_object_or_404(User, id=user_id)
    
    if user == request.user:
        messages.error(request, 'You cannot delete your own account.')
        return redirect('accounts:manage_users')
    
    if request.method == 'POST':
        result = account_service.delete_user_admin(user_id, request.user)
        
        if result['success']:
            messages.success(request, result['message'])
            return redirect('accounts:manage_users')
        else:
            messages.error(request, result['message'])
    
    context = {
        'user_obj': user,
    }
    
    return render(request, 'accounts/delete_user.html', context)
