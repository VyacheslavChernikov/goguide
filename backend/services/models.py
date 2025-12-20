from django.db import models
from business_units.models import BusinessUnit


class Service(models.Model):
    ROOM_TYPES = [
        ("Люкс", "Люкс"),
        ("Комфорт", "Комфорт"),
        ("Стандарт", "Стандарт"),
        ("Эконом", "Эконом"),
    ]

    business_unit = models.ForeignKey(
        BusinessUnit,
        on_delete=models.CASCADE,
        related_name="services",
        verbose_name="Площадка"
    )
    title = models.CharField(max_length=255, verbose_name="Название услуги")
    service_type = models.CharField(
        max_length=255,
        verbose_name="Тип услуги",
        choices=ROOM_TYPES,
        default="Стандарт",
        blank=True,
    )
    description = models.TextField(blank=True, verbose_name="Описание")
    price = models.DecimalField(max_digits=10, decimal_places=2, verbose_name="Цена")
    is_available = models.BooleanField(default=True, verbose_name="Доступна")
    photo_url = models.URLField(blank=True, null=True, verbose_name="URL фото")
    tour_widget = models.TextField(
        blank=True,
        null=True,
        verbose_name="Виджет 360/iframe",
        help_text="HTML-код виджета (например, GoGuide 360)",
    )

    class Meta:
        verbose_name = "Услуга"
        verbose_name_plural = "Услуги"

    def __str__(self):
        return f"{self.title} ({self.business_unit.name})"

    @property
    def photo_resolved_url(self):
        """
        Возвращает прямую ссылку на изображение, если в photo_url хранится ссылка
        на страницу freeimage.host, формирует прямой CDN iili.io.
        """
        if self.photo_url:
            url = self.photo_url.strip()
            if "freeimage.host" in url:
                slug = url.rstrip("/").split("/")[-1]
                slug = slug.split(".")[0]
                return f"https://iili.io/{slug}.png"
            return url
        return None
