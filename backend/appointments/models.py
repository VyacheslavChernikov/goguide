from django.db import models
from business_units.models import BusinessUnit
from services.models import Service


class Appointment(models.Model):
    STATUS_CHOICES = [
        ("pending", "Ожидает"),
        ("confirmed", "Подтверждено"),
        ("cancelled", "Отменено"),
    ]

    business_unit = models.ForeignKey(BusinessUnit, on_delete=models.CASCADE, verbose_name="Площадка")
    service = models.ForeignKey(Service, on_delete=models.CASCADE, verbose_name="Услуга/Номер")

    client_name = models.CharField(max_length=255, verbose_name="Имя клиента")
    client_phone = models.CharField(max_length=50, verbose_name="Телефон")
    client_email = models.EmailField(blank=True, null=True, verbose_name="Email")

    start_at = models.DateTimeField(verbose_name="Начало")
    end_at = models.DateTimeField(verbose_name="Окончание")

    total_price = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        verbose_name="Стоимость",
        blank=True,
        null=True,
    )
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default="pending", verbose_name="Статус")
    is_confirmed = models.BooleanField(default=False, verbose_name="Подтверждено")
    comment = models.TextField(blank=True, verbose_name="Комментарий")

    created_at = models.DateTimeField(auto_now_add=True, verbose_name="Создано")

    class Meta:
        verbose_name = "Запись"
        verbose_name_plural = "Записи"

    def __str__(self):
        return f"Запись #{self.id} — {self.client_name}"
