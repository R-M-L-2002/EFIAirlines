"""
Forms para el sistema de reservation.

Este archivo tiene los forms para crear, confirmar, cancelar reservas
y seleccionar asientos
"""
from django import forms
from django.core.exceptions import ValidationError
from django.utils import timezone
from datetime import timedelta

from .models import Reservation, Ticket
from apps.flights.models import Flight, Seat
from apps.passengers.models import Passenger


class NewReservationForm(forms.ModelForm):
    """
    Form para crear una reserva nueva
    """
    class Meta:
        model = Reservation
        fields = ['flight', 'passenger', 'seat']
        widgets = {
            # estos campos van ocultos porque se setean desde la view
            'flight': forms.HiddenInput(),
            'passenger': forms.HiddenInput(),
            'seat': forms.HiddenInput(),
        }

    def __init__(self, *args, **kwargs):
        self.user = kwargs.pop('user', None)
        self.flight_id = kwargs.pop('flight_id', None)
        super().__init__(*args, **kwargs)
        
        if self.flight_id:
            try:
                flight = Flight.objects.get(id=self.flight_id)
                self.fields['flight'].initial = flight
            except Flight.DoesNotExist:
                pass

    def clean_seat(self):
        seat = self.cleaned_data.get('seat')
        flight = self.cleaned_data.get('flight')
        if seat and flight:
            if seat.airplane != flight.airplane:
                raise ValidationError('The selected seat does not belong to this flight.')
            if seat.status == 'maintenance':
                raise ValidationError('The selected seat is under maintenance.')
            existing_reservation = Reservation.objects.filter(
                flight=flight,
                seat=seat,
                status__in=['confirmed', 'paid', 'completed']
            ).exists()
            if existing_reservation:
                raise ValidationError('The selected seat is already occupied.')
        return seat

    def clean_flight(self):
        flight = self.cleaned_data.get('flight')
        if flight:
            if flight.status not in ['scheduled', 'boarding']:
                raise ValidationError('This flight is not available for reservations.')
            if flight.departure_date <= timezone.now():
                raise ValidationError('Cannot reserve a flight that has already departed.')
        return flight

    def clean_passenger(self):
        passenger = self.cleaned_data.get('passenger')
        flight = self.cleaned_data.get('flight')
        if passenger and flight:
            existing_reservation = Reservation.objects.filter(
                flight=flight,
                passenger=passenger,
                status__in=['pending', 'confirmed', 'paid', 'completed']
            ).exists()
            if existing_reservation:
                raise ValidationError('You already have a reservation for this flight.')
        return passenger


class ConfirmReservationForm(forms.ModelForm):
    """
    Form para confirmar una reserva pendiente.
    Solo se requiere aceptar los términos.
    """
    accept_terms = forms.BooleanField(
        required=True,
        widget=forms.CheckboxInput(attrs={'class': 'form-check-input'}),
        label='I accept the terms and conditions'
    )

    class Meta:
        model = Reservation
        fields = [] 


class CancelReservationForm(forms.Form):
    """
    Form para cancelar una reserva
    """
    reason = forms.ChoiceField(
        choices=[
            ('change_of_plans', 'Change of Plans'),
            ('emergency', 'Emergency'),
            ('health_issue', 'Health Issue'),
            ('work_issue', 'Work Issue'),
            ('other', 'Other Reason'),
        ],
        widget=forms.Select(attrs={'class': 'form-control'}),
        label='Cancellation Reason'
    )
    comments = forms.CharField(
        required=False,
        widget=forms.Textarea(attrs={'class': 'form-control', 'rows': 3, 'placeholder': 'Additional comments (optional)'}),
        label='Comments'
    )
    confirm_cancellation = forms.BooleanField(
        required=True,
        widget=forms.CheckboxInput(attrs={'class': 'form-check-input'}),
        label='I confirm I want to cancel this reservation'
    )


class SeatSelectionForm(forms.Form):
    """
    Form para seleccionar asiento via AJAX
    """
    seat_id = forms.IntegerField(widget=forms.HiddenInput())
    flight_id = forms.IntegerField(widget=forms.HiddenInput())
    
    def clean_seat_id(self):
        seat_id = self.cleaned_data.get('seat_id')
        try:
            seat = Seat.objects.get(id=seat_id)
            if seat.status == 'maintenance':
                raise ValidationError('Seat under maintenance')
            return seat_id
        except Seat.DoesNotExist:
            raise ValidationError('Seat not found')
