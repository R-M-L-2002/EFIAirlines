from django.urls import path
from . import views

app_name = 'accounts' 

urlpatterns = [
    #Home
    path('', views.home, name='home'),
    
    #Autenticacion de user
    path('login/', views.login_user, name='login'),
    path('logout/', views.logout_user, name='logout'),
    path('register/', views.register_user, name='register'),
    
    #profile del user
    path('profile/', views.profile_user, name='profile'),
    path('profile/edit/', views.edit_profile, name='edit_profile'),
    path('profile/complete/', views.complete_profile, name='complete_profile'),
    path('dashboard/', views.dashboard_user, name='dashboard'),
    
    #AJAX
    path('verify-user/', views.verify_availability_user, name='verify_user'),
]
