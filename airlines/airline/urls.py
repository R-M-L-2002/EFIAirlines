"""
URL configuration for airline project.

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/5.2/topics/http/urls/
Examples:
Function views
    1. Add an import:  from my_app import views
    2. Add a URL to urlpatterns:  path('', views.home, name='home')
Class-based views
    1. Add an import:  from other_app.views import Home
    2. Add a URL to urlpatterns:  path('', Home.as_view(), name='home')
Including another URLconf
    1. Import the include() function: from django.urls import include, path
    2. Add a URL to urlpatterns:  path('blog/', include('blog.urls'))
"""
from django.contrib import admin
from django.urls import path, include
from django.conf import settings
from django.conf.urls.static import static

urlpatterns = [
    path('admin/', admin.site.urls),
    path('', include('apps.accounts.urls')),            
    path('flights/', include(('apps.flights.urls', 'flights'), namespace='flights')),    
    path('passengers/', include('apps.passengers.urls')), 
    path('reservations/', include('apps.reservations.urls')), 
    path('reports/', include('apps.reports.urls')),     
    path('auth/', include('django.contrib.auth.urls')), 
    
    path('api/', include('api.urls')),
]

if settings.DEBUG:
    # Esta línea asume que tienes MEDIA_URL y MEDIA_ROOT configurados en settings.py
    # Si no los tienes, esta línea no tendrá efecto o podría dar error.
    # La agregaré igualmente ya que estaba en tu original.
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)