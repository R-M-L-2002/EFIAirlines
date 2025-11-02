from django import forms
from apps.flights.models import Airplane, Flight

class AirplaneForm(forms.ModelForm):
    class Meta:
        model = Airplane
        fields = ['model', 'registration', 'capacity', 'rows', 'columns', 'active']


class FlightForm(forms.ModelForm):
    class Meta:
        model = Flight
        fields = ['flight_number', 'airplane', 'origin', 'destination',
                  'departure_date', 'arrival_date', 'status', 'base_price']
        widgets = {
            'departure_date': forms.DateTimeInput(attrs={'type': 'datetime-local'}),
            'arrival_date': forms.DateTimeInput(attrs={'type': 'datetime-local'}),
        }
