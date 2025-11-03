"""
Vistas para el sistema de reservas.

Este archivo contiene:
- Creación de nuevas reservas
- Gestión de reservas existentes
- Confirmación y cancelación
- Confirmación y pago unificado
- Generación de boletos
"""

from django.shortcuts import render, redirect
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.core.paginator import Paginator
from django.core.exceptions import ValidationError
from django.http import HttpResponse

from .forms import NewReservationForm, ConfirmReservationForm, CancelReservationForm
from .models import Reservation

from services.reservation import ReservationService, TicketService
from services.passenger import PassengerService

reservation_service = ReservationService()
ticket_service = TicketService()
passenger_service = PassengerService()


@login_required
def my_reservations(request):
    """Muestra todas las reservas del usuario logueado, con filtros y paginación."""
    try:
        passenger = passenger_service.get_passenger_by_email(request.user.email)
        if not passenger:
            messages.warning(request, 'Complete su perfil de pasajero antes de ver reservas.')
            return redirect('accounts:complete_profile')

        reservations = reservation_service.get_reservations_by_passenger(passenger.id)

        status_filter = request.GET.get('status', '')
        if status_filter:
            reservations = reservations.filter(status=status_filter)

        stats = reservation_service.get_passenger_stats(passenger.id)
        reservation_statuses = Reservation.STATUS_CHOICES

        paginator = Paginator(reservations, 6)
        page_number = request.GET.get('page')
        page_obj = paginator.get_page(page_number)

        return render(request, 'reservations/list.html', {
            'page_obj': page_obj,
            'reservation_statuses': reservation_statuses,
            'status_filter': status_filter,
            'stats': stats
        })

    except Exception:
        messages.error(request, 'Error al cargar las reservas.')
        return redirect('accounts:home')


@login_required
def new_reservation(request, flight_id):
    """Crea una reserva nueva con selección de asiento."""
    try:
        passenger = passenger_service.get_passenger_by_email(request.user.email)
        if not passenger:
            messages.warning(request, 'Complete su perfil antes de reservar.')
            return redirect('accounts:complete_profile')

        seat_data = reservation_service.get_available_seats_for_flight(flight_id)
        flight = seat_data['flight']
        seats_by_row = seat_data['seats_by_row']
        total_available = seat_data['total_available']

        if total_available == 0:
            messages.error(request, 'No hay asientos disponibles para este vuelo.')
            return redirect('flights:detail', flight_id=flight.id)

        if request.method == 'POST':
            selected_seat_id = request.POST.get('selected_seat')
            if not selected_seat_id:
                messages.error(request, 'Debe seleccionar un asiento.')
            else:
                try:
                    reservation = reservation_service.create_reservation(
                        flight_id=flight.id,
                        passenger_id=passenger.id,
                        seat_id=int(selected_seat_id),
                        notes=request.POST.get('notes', '')
                    )
                    messages.success(
                        request,
                        f'Reserva creada con éxito. Código: {reservation.reservation_code}'
                    )
                    return redirect('reservations:confirm_and_pay', reservation_code=reservation.reservation_code)
                except ValidationError as e:
                    messages.error(request, str(e))
                    return redirect('reservations:new', flight_id=flight.id)

        return render(request, 'reservations/new.html', {
            'flight': flight,
            'passenger': passenger,
            'seats_by_row': seats_by_row,
            'total_available': total_available,
        })

    except ValidationError as e:
        messages.error(request, str(e))
        return redirect('flights:list')
    except Exception:
        messages.error(request, 'Error al crear la reserva.')
        return redirect('flights:list')


@login_required
def reservation_detail(request, reservation_code):
    """Muestra detalle de la reserva y ticket si existe."""
    try:
        reservation = reservation_service.get_reservation_by_code(reservation_code)
        if not reservation:
            messages.error(request, 'Reserva no encontrada.')
            return redirect('reservations:my_reservations')

        ticket = None
        if reservation.status in ['paid', 'completed']:
            ticket = ticket_service.get_ticket_by_reservation_code(reservation_code)

        return render(request, 'reservations/detail.html', {
            'reservation': reservation,
            'ticket': ticket
        })

    except Exception:
        messages.error(request, 'Error al cargar la reserva.')
        return redirect('reservations:my_reservations')


@login_required
def cancel_reservation(request, reservation_code):
    """Cancela una reserva existente."""
    try:
        reservation = reservation_service.get_reservation_by_code(reservation_code)
        if not reservation:
            messages.error(request, 'Reserva no encontrada.')
            return redirect('reservations:my_reservations')

        if request.method == 'POST':
            form = CancelReservationForm(request.POST)
            if form.is_valid():
                try:
                    reservation_service.cancel_reservation(
                        reservation_code,
                        reason=form.cleaned_data['reason'],
                        comments=form.cleaned_data['comments']
                    )
                    messages.success(request, f'Reserva {reservation_code} cancelada exitosamente.')
                    return redirect('reservations:detail', reservation_code=reservation_code)
                except ValidationError as e:
                    messages.error(request, str(e))
        else:
            form = CancelReservationForm()

        return render(request, 'reservations/cancel.html', {
            'form': form,
            'reservation': reservation
        })

    except Exception:
        messages.error(request, 'Error al cancelar la reserva.')
        return redirect('reservations:my_reservations')


@login_required
def confirm_and_pay_reservation(request, reservation_code):
    """
    Confirma una reserva pendiente y procesa el pago.
    """
    try:
        # 🔹 Obtener la reserva y recargar relaciones críticas
        reservation = reservation_service.get_reservation_by_code(reservation_code)
        if not reservation:
            messages.error(request, 'Reserva no encontrada.')
            return redirect('reservations:my_reservations')

        try:
            reservation.refresh_from_db()  # asegura que seat y flight estén cargados
            _ = reservation.seat  # acceso forzado para detectar problemas de integridad
        except Reservation.seat.RelatedObjectDoesNotExist:
            messages.error(request, 'Error crítico: la reserva no tiene un asiento asignado.')
            return redirect('reservations:detail', reservation_code=reservation_code)

        # Validar usuario
        if reservation.passenger.email.lower() != request.user.email.lower():
            messages.error(request, 'No tiene permiso para esta reserva.')
            return redirect('reservations:my_reservations')

        # Verificar estado de la reserva
        if reservation.status == 'canceled':
            messages.error(request, 'La reserva ha sido cancelada.')
            return redirect('reservations:my_reservations')

        if reservation.status in ['completed', 'paid']:
            messages.info(request, 'La reserva ya ha sido pagada.')
            return redirect('reservations:detail', reservation_code=reservation_code)

            # Procesar formulario POST
        if request.method == 'POST':
            form = ConfirmReservationForm(request.POST)
            if form.is_valid():
                try:
                    # Confirmar reserva si está pendiente
                    if reservation.status == 'pending':
                        reservation_service.confirm_reservation(reservation_code)

                    # Procesar pago
                    reservation_service.process_payment(reservation_code, payment_method='credit_card')

                    messages.success(request, 'Reserva confirmada y pago exitoso. Ticket generado.')
                    return redirect('reservations:payment_success', reservation_code=reservation_code)

                except ValidationError as e:
                    messages.error(request, f'Error de validación: {str(e)}')
                except Exception as e:
                    import traceback
                    tb = traceback.format_exc()
                    messages.error(request, f'Error inesperado al procesar la reserva y el pago: {str(e)}\nTrace:\n{tb}')
            else:
                messages.error(request, 'Debe aceptar los términos y condiciones.')

        else:
            form = ConfirmReservationForm()

        return render(request, 'reservations/confirm.html', {
            'reservation': reservation,
            'form': form
        })


    except Exception as e:
        import traceback
        tb = traceback.format_exc()
        messages.error(request, f'Error crítico inesperado: {str(e)}\nTrace:\n{tb}')
        return redirect('reservations:my_reservations')


@login_required
def payment_success(request, reservation_code):
    """Vista de éxito mostrando ticket generado."""
    try:
        reservation = reservation_service.get_reservation_by_code(reservation_code)
        if not reservation or reservation.passenger.email != request.user.email:
            messages.error(request, 'Reserva no encontrada o acceso denegado.')
            return redirect('reservations:my_reservations')

        ticket = ticket_service.get_ticket_by_reservation_code(reservation_code)
        if not ticket:
            messages.error(request, 'No se encontró ticket para esta reserva.')
            return redirect('reservations:detail', reservation_code=reservation_code)

        return render(request, 'reservations/payment_success.html', {
            'reservation': reservation,
            'ticket': ticket
        })

    except Exception:
        messages.error(request, 'Error al cargar el ticket.')
        return redirect('reservations:my_reservations')


@login_required
def download_ticket_pdf(request, reservation_code):
    """Genera y descarga el ticket en PDF."""
    from reportlab.lib.pagesizes import letter
    from reportlab.lib.units import inch
    from reportlab.pdfgen import canvas
    from reportlab.lib import colors
    from io import BytesIO

    try:
        reservation = reservation_service.get_reservation_by_code(reservation_code)
        if not reservation or reservation.passenger.email != request.user.email:
            messages.error(request, 'Reserva no encontrada o acceso denegado.')
            return redirect('reservations:my_reservations')

        ticket = ticket_service.get_ticket_by_reservation_code(reservation_code)
        if not ticket:
            messages.error(request, 'No se encontró ticket para esta reserva.')
            return redirect('reservations:detail', reservation_code=reservation_code)

        # Crear PDF
        buffer = BytesIO()
        p = canvas.Canvas(buffer, pagesize=letter)
        width, height = letter

        p.setFont("Helvetica-Bold", 24)
        p.drawString(1*inch, height - 1*inch, "ELECTRONIC TICKET")

        p.setStrokeColor(colors.HexColor('#0066cc'))
        p.setLineWidth(2)
        p.line(1*inch, height - 1.3*inch, width - 1*inch, height - 1.3*inch)

        y = height - 2*inch
        p.setFont("Helvetica-Bold", 12)
        p.drawString(1*inch, y, "Ticket Number:")
        p.setFont("Helvetica", 12)
        p.drawString(3*inch, y, ticket.barcode)

        y -= 0.3*inch
        p.setFont("Helvetica-Bold", 12)
        p.drawString(1*inch, y, "Reservation Code:")
        p.setFont("Helvetica", 12)
        p.drawString(3*inch, y, reservation.reservation_code)

        # Información pasajero y vuelo
        y -= 0.6*inch
        p.setFont("Helvetica-Bold", 14)
        p.drawString(1*inch, y, "PASSENGER INFORMATION")
        y -= 0.3*inch
        p.setFont("Helvetica-Bold", 12)
        p.drawString(1*inch, y, "Name:")
        p.setFont("Helvetica", 12)
        p.drawString(3*inch, y, reservation.passenger.name)

        y -= 0.3*inch
        p.setFont("Helvetica-Bold", 12)
        p.drawString(1*inch, y, "Document:")
        p.setFont("Helvetica", 12)
        p.drawString(3*inch, y, f"{reservation.passenger.get_document_type_display()}: {reservation.passenger.document}")

        # Información vuelo
        y -= 0.6*inch
        p.setFont("Helvetica-Bold", 14)
        p.drawString(1*inch, y, "FLIGHT INFORMATION")
        y -= 0.3*inch
        p.setFont("Helvetica-Bold", 12)
        p.drawString(1*inch, y, "Flight Number:")
        p.setFont("Helvetica", 12)
        p.drawString(3*inch, y, reservation.flight.flight_number)

        y -= 0.3*inch
        p.setFont("Helvetica-Bold", 12)
        p.drawString(1*inch, y, "Route:")
        p.setFont("Helvetica", 12)
        p.drawString(3*inch, y, f"{reservation.flight.origin} → {reservation.flight.destination}")

        y -= 0.3*inch
        p.setFont("Helvetica-Bold", 12)
        p.drawString(1*inch, y, "Departure:")
        p.setFont("Helvetica", 12)
        p.drawString(3*inch, y, reservation.flight.departure_date.strftime("%B %d, %Y at %H:%M"))

        y -= 0.3*inch
        p.setFont("Helvetica-Bold", 12)
        p.drawString(1*inch, y, "Arrival:")
        p.setFont("Helvetica", 12)
        p.drawString(3*inch, y, reservation.flight.arrival_date.strftime("%B %d, %Y at %H:%M"))

        # Asiento
        y -= 0.6*inch
        p.setFont("Helvetica-Bold", 14)
        p.drawString(1*inch, y, "SEAT INFORMATION")
        y -= 0.3*inch
        p.setFont("Helvetica-Bold", 12)
        p.drawString(1*inch, y, "Seat Number:")
        p.setFont("Helvetica", 12)
        p.drawString(3*inch, y, reservation.seat.seat_number)

        # Precio
        y -= 0.6*inch
        p.setFont("Helvetica-Bold", 14)
        p.drawString(1*inch, y, "PAYMENT INFORMATION")
        y -= 0.3*inch
        p.setFont("Helvetica-Bold", 12)
        p.drawString(1*inch, y, "Total Price:")
        p.setFont("Helvetica", 12)
        p.drawString(3*inch, y, f"${reservation.total_price}")

        # Barcode
        y -= 0.6*inch
        p.setFont("Helvetica-Bold", 14)
        p.drawString(1*inch, y, "BARCODE")
        y -= 0.3*inch
        p.setFont("Courier-Bold", 16)
        p.drawString(1*inch, y, ticket.barcode)

        p.setFont("Helvetica-Oblique", 10)
        p.drawString(1*inch, 1*inch, "Llegue al aeropuerto al menos 2 horas antes de la salida.")
        p.drawString(1*inch, 0.7*inch, f"Fecha de emisión: {ticket.issue_date.strftime('%B %d, %Y at %H:%M')}")

        p.showPage()
        p.save()

        buffer.seek(0)
        response = HttpResponse(buffer, content_type='application/pdf')
        response['Content-Disposition'] = f'attachment; filename="ticket_{reservation.reservation_code}.pdf"'
        return response

    except Exception:
        messages.error(request, 'Error al generar el PDF.')
        return redirect('reservations:my_reservations')
