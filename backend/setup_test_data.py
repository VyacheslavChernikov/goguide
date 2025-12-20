#!/usr/bin/env python
import os
import django
from django.conf import settings

# Setup Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings')
django.setup()

from django.contrib.auth.models import User
from hotels.models import Hotel
from rooms.models import Room
from bookings.models import Booking
from hotel_portal.models import HotelUser, AISettings
from datetime import datetime, timedelta
import random

def setup_test_data():
    print("Setting up test data...")

    # Create test hotel if it doesn't exist
    hotel, created = Hotel.objects.get_or_create(
        slug='test-hotel',
        defaults={
            'name': 'Тестовый отель',
            'address': 'г. Москва, ул. Тестовая, 1',
            'description': 'Тестовый отель для демонстрации SmartHotel 360',
            'photo_url': 'https://example.com/hotel.jpg'
        }
    )
    print(f"Hotel {'created' if created else 'exists'}: {hotel.name}")

    # Create test user
    user, created = User.objects.get_or_create(
        username='admin',
        defaults={
            'email': 'admin@test.com',
            'is_staff': True,
            'is_superuser': True
        }
    )
    if created:
        user.set_password('admin')
        user.save()
    print(f"User {'created' if created else 'exists'}: {user.username}")

    # Link user to hotel
    hotel_user, created = HotelUser.objects.get_or_create(
        user=user,
        defaults={'hotel': hotel}
    )
    print(f"HotelUser {'created' if created else 'exists'}")

    # Create AI settings
    ai_settings, created = AISettings.objects.get_or_create(
        hotel=hotel,
        defaults={
            'bot_name': 'SmartHotel AI',
            'tone': 'дружелюбный',
            'system_prompt': 'Вы — AI-консьерж отеля SmartHotel 360. Помогайте гостям с информацией об отеле, бронировании номеров и рекомендациями.'
        }
    )
    print(f"AI Settings {'created' if created else 'exists'}")

    # Create test rooms
    room_types = ['Стандарт', 'Комфорт', 'Люкс', 'Президентский']
    for i in range(1, 11):
        room, created = Room.objects.get_or_create(
            hotel=hotel,
            room_number=i,
            defaults={
                'room_type': random.choice(room_types),
                'price_per_night': random.randint(3000, 15000),
                'is_available': random.choice([True, True, True, False])  # 75% available
            }
        )
        if created:
            print(f"Room created: {room}")

    # Create test bookings
    rooms = list(Room.objects.filter(hotel=hotel))
    guest_names = ['Иван Иванов', 'Мария Петрова', 'Алексей Сидоров', 'Елена Козлова', 'Дмитрий Новиков']

    for i in range(20):
        room = random.choice(rooms)
        guest_name = random.choice(guest_names)
        days_ahead = random.randint(-30, 30)

        check_in = datetime.now().date() + timedelta(days=days_ahead)
        check_out = check_in + timedelta(days=random.randint(1, 7))

        booking, created = Booking.objects.get_or_create(
            hotel=hotel,
            room=room,
            guest_name=guest_name,
            date_from=check_in,
            date_to=check_out,
            defaults={
                'guest_phone': f'+7 (999) {random.randint(100, 999)}-{random.randint(10, 99)}-{random.randint(10, 99)}',
                'guest_email': f'{guest_name.lower().replace(" ", ".")}@example.com',
                'total_price': (check_out - check_in).days * room.price_per_night,
                'is_confirmed': random.choice([True, True, False])  # 66% confirmed
            }
        )
        if created:
            print(f"Booking created: {booking}")

    print("Test data setup completed!")
    print("\nLogin credentials:")
    print("Username: admin")
    print("Password: admin")
    print("URL: http://localhost:8000/login/")

if __name__ == '__main__':
    setup_test_data()



