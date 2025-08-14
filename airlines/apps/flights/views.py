from django.shortcuts import render, get_object_or_404
from .models import Flight

def flight_list(request):
    flights = Flight.objects.all()
    return render(request, 'flights/flight_list.html', {'flights': flights})

def flight_detail(request, pk):
    flight = get_object_or_404(Flight, pk=pk)
    return render(request, 'flights/flight_detail.html', {'flight': flight})