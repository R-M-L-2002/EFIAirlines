"""
Forms for the reservation system.

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
        # agarramos el user y el flight_id si vienen de la view
        self.user = kwargs.pop('user', None)
        self.flight_id = kwargs.pop('flight_id', None)
        super().__init__(*args, **kwargs)
        
        # si viene un vuelo seteamos como inicial
        if self.flight_id:
            try:
                flight = Flight.objects.get(id=self.flight_id)
                self.fields['flight'].initial = flight
            except Flight.DoesNotExist:
                pass

    def clean_seat(self):
        """
        Validamos que el asiento este disponible para este vuelo
        """
        seat = self.cleaned_data.get('seat')
        flight = self.cleaned_data.get('flight')
        
        if seat and flight:
            # chequeamos que el asiento sea del avion del vuelo
            if seat.airplane != flight.airplane:
                raise ValidationError('The selected seat does not belong to this flight.')
            
            # chequeamos que no este en mantenimiento
            if seat.status == 'maintenance':
                raise ValidationError('The selected seat is under maintenance.')
            
            # chequeamos que no haya otra reserva para ese asiento en este vuelo
            existing_reservation = Reservation.objects.filter(
                flight=flight,
                seat=seat,
                status__in=['confirmed', 'paid', 'completed']
            ).exists()
            
            if existing_reservation:
                raise ValidationError('The selected seat is already occupied.')
        
        return seat

    def clean_flight(self):
        """
        Validamos que el vuelo este disponible para reservar
        """
        flight = self.cleaned_data.get('flight')
        
        if flight:
            # chequeamos que el estado del vuelo permita reservas
            if flight.status not in ['scheduled', 'boarding']:
                raise ValidationError('This flight is not available for reservations.')
            
            # chequeamos que la fecha de salida no haya pasado
            if flight.departure_date <= timezone.now():
                raise ValidationError('Cannot reserve a flight that has already departed.')
        
        return flight

    def clean_passenger(self):
        """
        Validamos que el pasajero no tenga ya una reserva para este vuelo
        """
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


class ConfirmReservationForm(forms.Form):
    """
    Form para confirmar una reserva pendiente
    """
    # check si acepta terminos
    accept_terms = forms.BooleanField(
        required=True,
        widget=forms.CheckboxInput(attrs={'class': 'form-check-input'}),
        label='I accept the terms and conditions'
    )
    
    # metodo de pago
    payment_method = forms.ChoiceField(
        choices=[
            ('card', 'Credit/Debit Card'),
            ('bank_transfer', 'Bank Transfer'),
            ('cash', 'Cash at Office'),
        ],
        widget=forms.Select(attrs={'class': 'form-control'}),
        label='Payment Method'
    )
    
    # notas sobre el pago, opcional
    payment_notes = forms.CharField(
        required=False,
        widget=forms.Textarea(attrs={
            'class': 'form-control',
            'rows': 2,
            'placeholder': 'Notes about the payment (optional)'
        }),
        label='Notes'
    )


class CancelReservationForm(forms.Form):
    """
    Form para cancelar una reserva
    """
    # motivo de cancelacion
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
    
    # comentarios opcionales
    comments = forms.CharField(
        required=False,
        widget=forms.Textarea(attrs={
            'class': 'form-control',
            'rows': 3,
            'placeholder': 'Additional comments (optional)'
        }),
        label='Comments'
    )
    
    # checkbox para confirmar que realmente quiere cancelar
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
        """
        Validamos que el asiento exista y este disponible
        """
        seat_id = self.cleaned_data.get('seat_id')
        
        try:
            seat = Seat.objects.get(id=seat_id)
            
            # chequeo de disponibilidad
            if seat.status == 'maintenance':
                raise ValidationError('Seat under maintenance')
            
            return seat_id
            
        except Seat.DoesNotExist:
            raise ValidationError('Seat not found')
