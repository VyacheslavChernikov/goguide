from django.db import models
from django.contrib.auth.models import User
from django.utils import timezone
from business_units.models import BusinessUnit


class BusinessUnitUser(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE, verbose_name="Пользователь")
    business_unit = models.ForeignKey(BusinessUnit, on_delete=models.CASCADE, verbose_name="Площадка")

    class Meta:
        verbose_name = "Пользователь площадки"
        verbose_name_plural = "Пользователи площадок"

    def __str__(self):
        return f"{self.user.username} -> {self.business_unit.name}"
