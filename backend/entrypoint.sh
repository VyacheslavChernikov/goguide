#!/bin/bash
set -e

echo "💾 Выполняю миграции Django..."
python manage.py makemigrations
python manage.py migrate --noinput

echo "👑 Проверяю суперпользователя..."
python manage.py shell <<EOF
from django.contrib.auth.models import User

if not User.objects.filter(username="admin").exists():
    User.objects.create_superuser("admin", "admin@example.com", "admin")
    print("✔ Суперпользователь создан (admin / admin)")
else:
    print("✔ Суперпользователь уже существует")
EOF


echo "🏨 Создаю тестовые площадки и услуги..."
python manage.py shell <<EOF
from business_units.models import BusinessUnit
from services.models import Service
from django.utils.text import slugify
import secrets

unit_names = ["Demo Площадка", "Go&Guide Студия", "Мастерская Байкал"]

for name in unit_names:
    slug = slugify(name)

    unit, created = BusinessUnit.objects.get_or_create(
        slug=slug,
        defaults={
            "name": name,
            "address": "",
            "description": "",
            "api_key": secrets.token_hex(32),
        }
    )
    if created:
        print(f"Создана площадка: {name}")
    else:
        print(f"Площадка уже существует: {name}")

    # создаём 3 услуги
    for i in range(1, 4):
        Service.objects.get_or_create(
            business_unit=unit,
            title=f"Услуга {i}",
            defaults={
                "service_type": "Стандарт",
                "price": 3500 + i * 500,
                "is_available": True
            }
        )
EOF

echo "🚀 Запуск Django..."
python manage.py runserver 0.0.0.0:8000
