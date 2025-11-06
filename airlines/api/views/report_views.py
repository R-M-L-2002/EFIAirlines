"""
ViewSets para reportes y estadísticas.
"""
from rest_framework import viewsets, status
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.permissions import IsAdminUser
from django.utils import timezone
from datetime import timedelta

from services.report import ReportService


class ReportViewSet(viewsets.ViewSet):
    """
    ViewSet para reportes y análisis.
    Solo administradores tienen acceso.
    
    passengers_by_flight: Listado de pasajeros por vuelo
    active_reservations: Reservas activas de un pasajero
    income_report: Reporte de ingresos por período
    dashboard_stats: Estadísticas generales del dashboard
    """
    permission_classes = [IsAdminUser]
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.service = ReportService()
    
    @action(detail=False, methods=['get'])
    def passengers_by_flight(self, request):
        """
        Obtener listado de pasajeros por vuelo.
        Query param: flight_id
        """
        flight_id = request.query_params.get('flight_id')
        
        if not flight_id:
            return Response(
                {'error': 'flight_id is required'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        try:
            report = self.service.get_flight_passengers_report(flight_id)
            
            if not report.get('success', True):
                return Response(
                    {'error': report.get('message', 'Error generating report')},
                    status=status.HTTP_404_NOT_FOUND
                )
            
            # Serializar las reservas
            from api.serializers import ReservationSerializer
            reservations_data = ReservationSerializer(
                report['reservations'], many=True
            ).data
            
            return Response({
                'flight': {
                    'id': report['flight'].id,
                    'flight_number': report['flight'].flight_number,
                    'origin': report['flight'].origin,
                    'destination': report['flight'].destination,
                    'departure_date': report['flight'].departure_date,
                    'arrival_date': report['flight'].arrival_date,
                },
                'reservations': reservations_data,
                'statistics': {
                    'total_reservations': report['total_reservations'],
                    'confirmed_reservations': report['confirmed_reservations'],
                    'total_income': float(report['total_income']),
                    'seat_distribution': report['seat_distribution'],
                    'occupancy_percent': report['occupancy_percent']
                }
            })
        except Exception as e:
            return Response(
                {'error': str(e)},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )
    
    @action(detail=False, methods=['get'])
    def active_reservations(self, request):
        """
        Obtener reservas activas de un pasajero.
        Query param: passenger_id
        """
        passenger_id = request.query_params.get('passenger_id')
        
        if not passenger_id:
            return Response(
                {'error': 'passenger_id is required'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        try:
            from services.reservation import ReservationService
            from api.serializers import ReservationSerializer
            
            reservation_service = ReservationService()
            reservations = reservation_service.get_reservations_by_passenger(passenger_id)
            
            # Filtrar solo activas
            active_reservations = reservations.filter(
                status__in=['confirmed', 'paid']
            )
            
            serializer = ReservationSerializer(active_reservations, many=True)
            return Response({
                'passenger_id': passenger_id,
                'active_reservations': serializer.data,
                'total_active': active_reservations.count()
            })
        except Exception as e:
            return Response(
                {'error': str(e)},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )
    
    @action(detail=False, methods=['get'])
    def income_report(self, request):
        """
        Reporte de ingresos por período.
        Query params: start_date, end_date (formato: YYYY-MM-DD)
        """
        start_date_str = request.query_params.get('start_date')
        end_date_str = request.query_params.get('end_date')
        
        try:
            from datetime import datetime
            
            # Parsear fechas
            start_date = None
            end_date = None
            
            if start_date_str:
                start_date = datetime.strptime(start_date_str, '%Y-%m-%d')
                start_date = timezone.make_aware(start_date)
            
            if end_date_str:
                end_date = datetime.strptime(end_date_str, '%Y-%m-%d')
                end_date = timezone.make_aware(end_date)
            
            report = self.service.get_income_report(start_date, end_date)
            
            return Response({
                'period': {
                    'start_date': report['start_date'].strftime('%Y-%m-%d'),
                    'end_date': report['end_date'].strftime('%Y-%m-%d')
                },
                'summary': {
                    'total_income': float(report['total_income']),
                    'total_reservations': report['total_reservations'],
                    'average_income': float(report['average_income'])
                },
                'daily_income': [
                    {
                        'date': item['date'].strftime('%Y-%m-%d'),
                        'total': float(item['total']),
                        'count': item['count']
                    }
                    for item in report['daily_income']
                ],
                'income_by_type': [
                    {
                        'seat_type': item['seat_type'],
                        'total': float(item['total']),
                        'count': item['count']
                    }
                    for item in report['income_by_type']
                ]
            })
        except ValueError as e:
            return Response(
                {'error': 'Invalid date format. Use YYYY-MM-DD'},
                status=status.HTTP_400_BAD_REQUEST
            )
        except Exception as e:
            return Response(
                {'error': str(e)},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )
    
    @action(detail=False, methods=['get'])
    def dashboard_stats(self, request):
        """Obtener estadísticas generales del dashboard"""
        try:
            stats = self.service.get_dashboard_statistics()
            
            return Response({
                'totals': {
                    'flights': stats['total_flights'],
                    'passengers': stats['total_passengers'],
                    'reservations': stats['total_reservations'],
                    'users': stats['total_users']
                },
                'reservations_by_status': stats['reservations_by_status'],
                'popular_flights': [
                    {
                        'id': flight.id,
                        'flight_number': flight.flight_number,
                        'origin': flight.origin,
                        'destination': flight.destination,
                        'reservations_count': flight.reservations_count
                    }
                    for flight in stats['popular_flights']
                ],
                'monthly_income': stats['monthly_income'],
                'flight_occupancy': [
                    {
                        'flight': {
                            'id': item['flight'].id,
                            'flight_number': item['flight'].flight_number,
                            'origin': item['flight'].origin,
                            'destination': item['flight'].destination
                        },
                        'occupancy': item['occupancy']
                    }
                    for item in stats['flight_occupancy']
                ]
            })
        except Exception as e:
            return Response(
                {'error': str(e)},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )
