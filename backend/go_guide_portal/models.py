from django.db import models
from django.contrib.auth.models import User
from django.utils import timezone
from business_units.models import BusinessUnit


class KnowledgeFile(models.Model):
    business_unit = models.ForeignKey(BusinessUnit, on_delete=models.CASCADE, related_name="knowledge_files", verbose_name="Площадка")
    filename = models.CharField(max_length=255, verbose_name="Имя файла")
    content_hash = models.CharField(max_length=64, verbose_name="Хэш содержимого")
    uploaded_at = models.DateTimeField(default=timezone.now, verbose_name="Загружен")

    class Meta:
        verbose_name = "Файл базы знаний"
        verbose_name_plural = "Файлы базы знаний"

    def __str__(self):
        return f"{self.filename} ({self.business_unit.name})"


class BusinessUnitUser(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE, verbose_name="Пользователь")
    business_unit = models.ForeignKey(BusinessUnit, on_delete=models.CASCADE, verbose_name="Площадка")

    class Meta:
        verbose_name = "Пользователь площадки"
        verbose_name_plural = "Пользователи площадок"

    def __str__(self):
        return f"{self.user.username} -> {self.business_unit.name}"


class KnowledgeDocument(models.Model):
    STATUS_CHOICES = [
        ("pending", "Ожидает обработки"),
        ("processed", "Обработан"),
        ("failed", "Ошибка"),
    ]

    business_unit = models.ForeignKey(BusinessUnit, on_delete=models.CASCADE, related_name="knowledge_documents", verbose_name="Площадка")
    file = models.FileField(upload_to="ai_knowledge/", verbose_name="Файл")
    original_name = models.CharField(max_length=255, verbose_name="Имя файла")
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default="pending", verbose_name="Статус")
    uploaded_at = models.DateTimeField(default=timezone.now, verbose_name="Загружен")

    class Meta:
        verbose_name = "Документ базы знаний"
        verbose_name_plural = "Документы базы знаний"

    def __str__(self):
        return f"{self.original_name} ({self.business_unit.name})"
