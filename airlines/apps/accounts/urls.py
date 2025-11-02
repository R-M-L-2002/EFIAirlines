"""
URLs for the accounts app (main page and authentication)
"""
from django.urls import path
from . import views

app_name = 'accounts'

urlpatterns = [
    # Main page
    path('', views.home, name='home'),
    
    # Authentication
    path('login/', views.user_login, name='login'),
    path('logout/', views.user_logout, name='logout'),
    path('register/', views.user_registration, name='register'),
    
    # User profile
    path('profile/', views.user_profile, name='profile'),
    path('profile/edit/', views.edit_profile, name='edit_profile'),
    path('profile/complete/', views.complete_profile, name='complete_profile'),
    path('dashboard/', views.user_dashboard, name='dashboard'),
    
    # AJAX
    path('check-username/', views.check_username_availability, name='check_username'),
    
    # User Management (Admin only)
    path('users/', views.manage_users, name='manage_users'),
    path('users/create/', views.create_user, name='create_user'),
    path('users/<int:user_id>/edit/', views.edit_user, name='edit_user'),
    path('users/<int:user_id>/delete/', views.delete_user, name='delete_user'),
]
