from django import forms
from django.contrib.auth.forms import PasswordChangeForm

from services.models import Service
from appointments.models import Appointment
from business_units.models import BusinessUnit, PayoutRequest


class GigaChatSettingsForm(forms.ModelForm):
    class Meta:
        model = BusinessUnit
        fields = ["gigachat_client_id", "gigachat_auth_key", "gigachat_scope"]
        base_input = "w-full px-3 py-2 rounded-lg bg-panel border border-white/10 text-text placeholder-muted focus:outline-none focus:ring-2 focus:ring-accent"
        widgets = {
            "gigachat_client_id": forms.TextInput(attrs={"class": base_input, "autocomplete": "off", "placeholder": "Client ID"}),
            "gigachat_auth_key": forms.PasswordInput(attrs={"class": base_input, "autocomplete": "off", "placeholder": "Authorization key"}),
            "gigachat_scope": forms.TextInput(attrs={"class": base_input, "placeholder": "GIGACHAT_API_PERS"}),
        }


class ServiceForm(forms.ModelForm):
    class Meta:
        model = Service
        fields = ["title", "service_type", "price", "description", "photo_url", "tour_widget", "is_available"]
        base_input = "w-full px-3 py-2 rounded-lg bg-panel border border-white/10 text-text placeholder-muted focus:outline-none focus:ring-2 focus:ring-accent"
        widgets = {
            "title": forms.TextInput(attrs={"class": base_input, "required": True, "placeholder": "Например, Номер 101"}),
            "service_type": forms.Select(attrs={"class": f"{base_input} pr-8"}),
            "price": forms.NumberInput(attrs={"class": base_input, "step": "0.01", "min": "0"}),
            "description": forms.Textarea(attrs={"class": f"{base_input} min-h-[100px]", "rows": 3}),
            "photo_url": forms.URLInput(attrs={"class": base_input, "placeholder": "https://..."}),
            "tour_widget": forms.Textarea(
                attrs={
                    "class": f"{base_input} min-h-[120px] font-mono text-xs",
                    "rows": 4,
                    "placeholder": '<div class="goguide-tour-widget"...></div>',
                }
            ),
            "is_available": forms.CheckboxInput(attrs={"class": "h-4 w-4 text-accent border-white/20 rounded"}),
        }


class AppointmentForm(forms.ModelForm):
    class Meta:
        model = Appointment
        fields = [
            "client_name",
            "client_phone",
            "client_email",
            "service",
            "start_at",
            "end_at",
            "total_price",
            "status",
            "comment",
        ]
        base_input = "w-full px-3 py-2 rounded-lg bg-panel border border-white/10 text-text placeholder-muted focus:outline-none focus:ring-2 focus:ring-accent"
        widgets = {
            "client_name": forms.TextInput(attrs={"class": base_input, "required": True}),
            "client_phone": forms.TextInput(attrs={"class": base_input, "required": True}),
            "client_email": forms.EmailInput(attrs={"class": base_input}),
            "service": forms.Select(attrs={"class": f"{base_input} pr-8"}),
            "start_at": forms.DateTimeInput(
                format="%Y-%m-%dT%H:%M",
                attrs={"type": "datetime-local", "class": base_input, "required": True},
            ),
            "end_at": forms.DateTimeInput(
                format="%Y-%m-%dT%H:%M",
                attrs={"type": "datetime-local", "class": base_input, "required": True},
            ),
            "total_price": forms.NumberInput(attrs={"class": base_input, "step": "0.01", "min": "0"}),
            "status": forms.Select(attrs={"class": f"{base_input} pr-8"}),
            "comment": forms.Textarea(attrs={"class": f"{base_input} min-h-[100px]", "rows": 3}),
        }

    def clean(self):
        cleaned = super().clean()
        start_at = cleaned.get("start_at")
        end_at = cleaned.get("end_at")
        if start_at and end_at and end_at < start_at:
            raise forms.ValidationError("Окончание не может быть раньше начала.")
        # Если цена не указана в форме, подставляем из инстанса (редактирование) или из услуги
        total_price = cleaned.get("total_price")
        service = cleaned.get("service")
        if total_price in (None, ""):
            if self.instance and self.instance.pk and self.instance.total_price is not None:
                cleaned["total_price"] = self.instance.total_price
            elif service and service.price is not None:
                cleaned["total_price"] = service.price

        # Проверка пересечений по времени для той же услуги (и площадки)
        if service and start_at and end_at:
            qs = Appointment.objects.filter(
                service=service,
                business_unit=service.business_unit,
            ).exclude(status="cancelled")
            if self.instance and self.instance.pk:
                qs = qs.exclude(pk=self.instance.pk)
            overlap = qs.filter(start_at__lt=end_at, end_at__gt=start_at).exists()
            if overlap:
                raise forms.ValidationError("В это время услуга уже занята (пересечение с другой записью).")

        return cleaned

    def save(self, commit=True):
        instance = super().save(commit=False)
        instance.is_confirmed = instance.status == "confirmed"
        if commit:
            instance.save()
            self.save_m2m()
        return instance

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        dt_formats = ["%Y-%m-%dT%H:%M", "%Y-%m-%d %H:%M", "%d.%m.%Y %H:%M"]
        for fname in ["start_at", "end_at"]:
            if fname in self.fields:
                self.fields[fname].input_formats = dt_formats


class BusinessUnitForm(forms.ModelForm):
    class Meta:
        model = BusinessUnit
        fields = [
            "name",
            "address",
            "phone",
            "email",
            "website",
            "socials",
            "working_hours_from",
            "working_hours_to",
            "checkin_time",
            "checkout_time",
            "parking_info",
            "wifi_info",
            "meals_info",
            "kids_policy",
            "pets_policy",
            "smoke_policy",
            "accessibility",
            "coordinates",
            "positioning",
            "tone",
            "allow_emoji",
            "description",
            "photo_url",
            "widget_config",
            "portal_theme",
            "payout_method",
            "payout_account",
            "payout_bank",
            "payout_bik",
            "payout_inn",
            "payout_kpp",
            "payout_name",
            "payout_provider",
            "payout_mode",
            "payout_provider_key",
            "payout_provider_secret",
            "payout_webhook_secret",
        ]
        base_input = "w-full px-3 py-2 rounded-lg bg-panel border border-white/10 text-text placeholder-muted focus:outline-none focus:ring-2 focus:ring-accent"
        widgets = {
            "name": forms.TextInput(attrs={"class": base_input, "required": True}),
            "address": forms.TextInput(attrs={"class": base_input}),
            "phone": forms.TextInput(attrs={"class": base_input, "placeholder": "+7 ..."}),
            "email": forms.EmailInput(attrs={"class": base_input, "placeholder": "info@example.com"}),
            "website": forms.URLInput(attrs={"class": base_input, "placeholder": "https://"}),
            "socials": forms.Textarea(attrs={"class": f"{base_input} min-h-[80px]", "rows": 2, "placeholder": "Ссылки через запятую"}),
            "working_hours_from": forms.TimeInput(
                format="%H:%M", attrs={"class": base_input, "type": "time", "step": "60", "placeholder": "09:00"}
            ),
            "working_hours_to": forms.TimeInput(
                format="%H:%M", attrs={"class": base_input, "type": "time", "step": "60", "placeholder": "21:00"}
            ),
            "checkin_time": forms.TimeInput(
                format="%H:%M", attrs={"class": base_input, "type": "time", "step": "60", "placeholder": "14:00"}
            ),
            "checkout_time": forms.TimeInput(
                format="%H:%M", attrs={"class": base_input, "type": "time", "step": "60", "placeholder": "12:00"}
            ),
            "parking_info": forms.TextInput(attrs={"class": base_input, "placeholder": "Бесплатная/платная/нет"}),
            "wifi_info": forms.TextInput(attrs={"class": base_input, "placeholder": "Скорость, пароль, условия"}),
            "meals_info": forms.TextInput(attrs={"class": base_input, "placeholder": "Завтрак/обеды/ужины/кухня"}),
            "kids_policy": forms.TextInput(attrs={"class": base_input, "placeholder": "Дети до 5 бесплатно / есть детская кроватка"}),
            "pets_policy": forms.TextInput(attrs={"class": base_input, "placeholder": "Можно/нельзя, доплата"}),
            "smoke_policy": forms.TextInput(attrs={"class": base_input, "placeholder": "Запрет/места для курения"}),
            "accessibility": forms.TextInput(attrs={"class": base_input, "placeholder": "Пандус, лифт, доступная среда"}),
            "coordinates": forms.TextInput(attrs={"class": base_input, "placeholder": "55.7558, 37.6176 или описание проезда"}),
            "positioning": forms.Textarea(attrs={"class": f"{base_input} min-h-[100px]", "rows": 3, "placeholder": "УТП, сегменты, ценностное предложение"}),
            "tone": forms.Select(attrs={"class": f"{base_input} pr-8"}),
            "allow_emoji": forms.CheckboxInput(attrs={"class": "h-4 w-4 text-accent border-white/20 rounded"}),
            "description": forms.Textarea(attrs={"class": f"{base_input} min-h-[100px]", "rows": 3}),
            "photo_url": forms.URLInput(attrs={"class": base_input, "placeholder": "https://..."}),
            "widget_config": forms.HiddenInput(),
            "portal_theme": forms.Select(attrs={"class": f"{base_input} pr-8"}, choices=[("dark", "Dark"), ("light", "Light")]),
            "payout_method": forms.Select(attrs={"class": f"{base_input} pr-8"}, choices=[("bank", "Банковский счет"), ("sbp", "СБП / карта")]),
            "payout_account": forms.TextInput(attrs={"class": base_input, "placeholder": "Р/с или карта для выплат"}),
            "payout_bank": forms.TextInput(attrs={"class": base_input, "placeholder": "Банк"}),
            "payout_bik": forms.TextInput(attrs={"class": base_input, "placeholder": "БИК"}),
            "payout_inn": forms.TextInput(attrs={"class": base_input, "placeholder": "ИНН"}),
            "payout_kpp": forms.TextInput(attrs={"class": base_input, "placeholder": "КПП"}),
            "payout_name": forms.TextInput(attrs={"class": base_input, "placeholder": "Юр. наименование / ФИО"}),
            "payout_provider": forms.Select(
                attrs={"class": f"{base_input} pr-8"},
                choices=[
                    ("manual", "Ручной"),
                    ("mock", "Тестовый"),
                    ("yookassa", "YooKassa"),
                    ("cloudpayments", "CloudPayments"),
                    ("tinkoff", "Тинькофф"),
                ],
            ),
            "payout_mode": forms.Select(
                attrs={"class": f"{base_input} pr-8"},
                choices=[("test", "Тест"), ("live", "Боевой")],
            ),
            "payout_provider_key": forms.TextInput(attrs={"class": base_input, "placeholder": "ShopId/PublicId/TerminalKey"}),
            "payout_provider_secret": forms.PasswordInput(attrs={"class": base_input, "placeholder": "Secret / API key"}, render_value=True),
            "payout_webhook_secret": forms.PasswordInput(attrs={"class": base_input, "placeholder": "Секрет подписи вебхука"}, render_value=True),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Делим обязательные поля на форме (модель оставляем гибкой)
        for fname in ["email", "working_hours_from", "working_hours_to", "checkin_time", "checkout_time"]:
            if fname in self.fields:
                self.fields[fname].required = True
        # Подсказки
        self.fields["working_hours_from"].help_text = "Например: 09:00"
        self.fields["working_hours_to"].help_text = "Например: 21:00"
        self.fields["checkin_time"].help_text = "Например: 14:00"
        self.fields["checkout_time"].help_text = "Например: 12:00"


class PayoutRequestForm(forms.ModelForm):
    class Meta:
        model = PayoutRequest
        fields = ["amount", "comment"]
        base_input = "w-full px-3 py-2 rounded-lg bg-panel border border-white/10 text-text placeholder-muted focus:outline-none focus:ring-2 focus:ring-accent"
        widgets = {
            "amount": forms.NumberInput(attrs={"class": base_input, "step": "0.01", "min": "0", "placeholder": "Например, 5000"}),
            "comment": forms.Textarea(attrs={"class": f"{base_input} min-h-[80px]", "rows": 3, "placeholder": "Комментарий (необязательно)"}),
        }


class AdminPasswordForm(PasswordChangeForm):
    """
    Обёртка над стандартной формой смены пароля, чтобы стилизовать через Tailwind.
    """

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        for field in self.fields.values():
            field.widget.attrs.update({
                "class": "w-full px-3 py-2 rounded-lg bg-panel border border-white/10 text-text placeholder-muted focus:outline-none focus:ring-2 focus:ring-accent",
                "required": True,
            })

