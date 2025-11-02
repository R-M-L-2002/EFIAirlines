"""
Script para actualizar los precios extra de los asientos según su tipo.
Este script debe ejecutarse una vez para configurar los precios correctos.
"""

import os
import sys
import django

# Get the directory where this script is located
script_dir = os.path.dirname(os.path.abspath(__file__))
# Get the parent directory (airlines/)
parent_dir = os.path.dirname(script_dir)
# Add it to Python path
sys.path.insert(0, parent_dir)

# Configurar Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'airline.settings')
django.setup()

from apps.flights.models import Seat
from decimal import Decimal

def update_seat_prices():
    """
    Actualiza los precios extra de los asientos:
    - First Class: +$200,000
    - Business Class: +$100,000
    - Economy Class: $0 (sin cargo extra)
    """
    
    # Actualizar First Class
    first_class_count = Seat.objects.filter(type='first').update(
        extra_price=Decimal('200000.00')
    )
    print(f"✓ Updated {first_class_count} First Class seats with extra price: $200,000")
    
    # Actualizar Business Class
    business_class_count = Seat.objects.filter(type='business').update(
        extra_price=Decimal('100000.00')
    )
    print(f"✓ Updated {business_class_count} Business Class seats with extra price: $100,000")
    
    # Actualizar Economy Class (asegurar que sea 0)
    economy_class_count = Seat.objects.filter(type='economy').update(
        extra_price=Decimal('0.00')
    )
    print(f"✓ Updated {economy_class_count} Economy Class seats with no extra charge")
    
    print("\n✅ All seat prices have been updated successfully!")
    print("\nPrice structure:")
    print("  - First Class: Base price + $200,000")
    print("  - Business Class: Base price + $100,000")
    print("  - Economy Class: Base price only")

if __name__ == '__main__':
    print("Updating seat prices...\n")
    update_seat_prices()
