from django.db import models
from django.contrib.auth import get_user_model
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
    # Реквизиты для выплат (payout)
    payout_account = models.CharField(max_length=32, blank=True, verbose_name="Расчетный счет / карта для выплат")
    payout_bank = models.CharField(max_length=128, blank=True, verbose_name="Банк для выплат")
    payout_bik = models.CharField(max_length=16, blank=True, verbose_name="БИК")
    payout_inn = models.CharField(max_length=16, blank=True, verbose_name="ИНН")
    payout_kpp = models.CharField(max_length=16, blank=True, verbose_name="КПП")
    payout_name = models.CharField(max_length=255, blank=True, verbose_name="Юр. наименование / ФИО получателя")
    payout_method = models.CharField(
        max_length=16,
        default="bank",
        choices=[("bank", "Банковский счет"), ("sbp", "СБП / карта")],
        verbose_name="Способ выплат",
    )
    payout_provider = models.CharField(
        max_length=32,
        default="manual",
        choices=[
            ("manual", "Ручной"),
            ("mock", "Тестовый"),
            ("yookassa", "YooKassa Payouts"),
            ("cloudpayments", "CloudPayments Payouts"),
            ("tinkoff", "Тинькофф Выплаты"),
        ],
        verbose_name="Провайдер выплат",
    )
    payout_mode = models.CharField(
        max_length=8,
        default="test",
        choices=[("test", "Тест"), ("live", "Боевой")],
        verbose_name="Режим выплат",
    )
    payout_provider_key = models.CharField(max_length=255, blank=True, verbose_name="ID / Public / TerminalKey")
    payout_provider_secret = models.CharField(max_length=255, blank=True, verbose_name="Secret / API key")
    payout_webhook_secret = models.CharField(max_length=255, blank=True, verbose_name="Секрет для подписи вебхука")
    payout_provider_extra = models.JSONField(default=dict, blank=True, verbose_name="Доп. данные провайдера")

    def __str__(self):
        return self.name

    class Meta:
        verbose_name = "Площадка/Бизнес"
        verbose_name_plural = "Площадки/Бизнесы"


class PayoutRequest(models.Model):
    """
    Запрос на вывод средств (payout) для площадки.
    """

    STATUS_CHOICES = [
        ("pending", "На проверке"),
        ("processing", "В обработке"),
        ("paid", "Выплачено"),
        ("failed", "Ошибка"),
    ]

    PROVIDER_CHOICES = [
        ("manual", "Ручной"),
        ("mock", "Тестовый"),
        ("yookassa", "YooKassa Payouts"),
        ("cloudpayments", "CloudPayments Payouts"),
        ("tinkoff", "Тинькофф Выплаты"),
    ]

    business_unit = models.ForeignKey(
        BusinessUnit,
        on_delete=models.CASCADE,
        related_name="payouts",
        verbose_name="Площадка",
    )
    amount = models.DecimalField(max_digits=10, decimal_places=2, verbose_name="Сумма вывода")
    fee = models.DecimalField(max_digits=10, decimal_places=2, default=0, verbose_name="Комиссия")
    currency = models.CharField(max_length=3, default="RUB", verbose_name="Валюта")
    status = models.CharField(max_length=16, choices=STATUS_CHOICES, default="pending", verbose_name="Статус")
    provider = models.CharField(max_length=32, choices=PROVIDER_CHOICES, default="manual", verbose_name="Провайдер")
    provider_payout_id = models.CharField(max_length=128, blank=True, verbose_name="ID выплаты у провайдера")
    meta = models.JSONField(default=dict, blank=True, verbose_name="Метаданные/ответ провайдера")
    comment = models.TextField(blank=True, verbose_name="Комментарий")
    requested_by = models.ForeignKey(
        get_user_model(),
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
        verbose_name="Инициатор",
    )
    created_at = models.DateTimeField(auto_now_add=True, verbose_name="Создано")
    processed_at = models.DateTimeField(null=True, blank=True, verbose_name="Обработано")

    class Meta:
        verbose_name = "Выплата"
        verbose_name_plural = "Выплаты"
        ordering = ["-created_at"]

    def __str__(self):
        return f"Payout #{self.id} — {self.amount} {self.currency}"

    @property
    def amount_after_fee(self):
        try:
            return (self.amount or 0) - (self.fee or 0)
        except Exception:
            return self.amount

# Затем: python manage.py makemigrations && python manage.py migrate
