from django.db import models
import secrets


class BusinessUnit(models.Model):
    name = models.CharField(max_length=255, verbose_name="Название")
    slug = models.SlugField(unique=True, verbose_name="Слаг")
    api_key = models.CharField(max_length=64, unique=True, default=secrets.token_hex(32), verbose_name="API ключ")
    address = models.CharField(max_length=255, blank=True, verbose_name="Адрес")
    phone = models.CharField(max_length=32, blank=True, verbose_name="Телефон")
    email = models.EmailField(blank=True, verbose_name="E-mail")
    website = models.URLField(blank=True, verbose_name="Сайт")
    socials = models.TextField(blank=True, verbose_name="Соцсети/ссылки")
    working_hours_from = models.CharField(max_length=16, blank=True, verbose_name="Время открытия")
    working_hours_to = models.CharField(max_length=16, blank=True, verbose_name="Время закрытия")
    checkin_time = models.CharField(max_length=16, blank=True, verbose_name="Чек-ин")
    checkout_time = models.CharField(max_length=16, blank=True, verbose_name="Чек-аут")
    parking_info = models.CharField(max_length=255, blank=True, verbose_name="Парковка")
    wifi_info = models.CharField(max_length=255, blank=True, verbose_name="Wi‑Fi")
    meals_info = models.CharField(max_length=255, blank=True, verbose_name="Питание")
    kids_policy = models.CharField(max_length=255, blank=True, verbose_name="Детская политика/опции")
    pets_policy = models.CharField(max_length=255, blank=True, verbose_name="Политика по питомцам")
    smoke_policy = models.CharField(max_length=255, blank=True, verbose_name="Политика курения")
    accessibility = models.CharField(max_length=255, blank=True, verbose_name="Доступность/инклюзивность")
    coordinates = models.CharField(max_length=255, blank=True, verbose_name="Координаты/проезд")
    positioning = models.TextField(blank=True, verbose_name="УТП/позиционирование")
    TONE_CHOICES = [
        ("friendly", "Дружелюбный"),
        ("neutral", "Нейтральный"),
        ("formal", "Строгий"),
    ]
    tone = models.CharField(max_length=16, choices=TONE_CHOICES, default="friendly", verbose_name="Тон ассистента")
    allow_emoji = models.BooleanField(default=True, verbose_name="Разрешать эмодзи в ответах ассистента")
    description = models.TextField(blank=True, verbose_name="Описание")
    photo_url = models.URLField(blank=True, null=True, verbose_name="URL фото")
    BUSINESS_TYPES = [
        ('hotel', "Отели / Хостелы"),
        ('service', "Услуги (салон, СТО, врач)"),
        ('tour', "Туры / Экскурсии"),
        ('event', "Мероприятия / Билеты"),
        ('rent', "Аренда (авто, инвентарь)"),
    ]
    business_type = models.CharField(
        max_length=20,
        choices=BUSINESS_TYPES,
        default='service',
        verbose_name="Тип бизнеса",
    )
    gigachat_client_id = models.CharField(max_length=255, blank=True, null=True, verbose_name="GigaChat Client ID")
    gigachat_auth_key = models.CharField(max_length=512, blank=True, null=True, verbose_name="GigaChat Authorization Key (secret)")
    gigachat_scope = models.CharField(max_length=64, blank=True, null=True, default="GIGACHAT_API_PERS", verbose_name="GigaChat Scope")
    gigachat_key = models.TextField(blank=True, null=True, verbose_name="GigaChat Auth Key")  # legacy
    alice_key = models.TextField(blank=True, null=True, verbose_name="Yandex Alice API Key")
    widget_config = models.JSONField(default=dict, blank=True, verbose_name="Настройки виджета бронирования")
    portal_theme = models.CharField(max_length=16, default="dark", verbose_name="Тема портала (dark/light)")

    def __str__(self):
        return self.name

    class Meta:
        verbose_name = "Площадка/Бизнес"
        verbose_name_plural = "Площадки/Бизнесы"

# Затем: python manage.py makemigrations && python manage.py migrate
