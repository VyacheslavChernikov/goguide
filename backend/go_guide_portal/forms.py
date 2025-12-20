from django import forms
from django.contrib.auth.forms import PasswordChangeForm

from services.models import Service
from appointments.models import Appointment
from business_units.models import BusinessUnit


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
        fields = ["title", "service_type", "price", "description", "photo_url", "is_available"]
        base_input = "w-full px-3 py-2 rounded-lg bg-panel border border-white/10 text-text placeholder-muted focus:outline-none focus:ring-2 focus:ring-accent"
        widgets = {
            "title": forms.TextInput(attrs={"class": base_input, "required": True, "placeholder": "Например, Номер 101"}),
            "service_type": forms.Select(attrs={"class": f"{base_input} pr-8"}),
            "price": forms.NumberInput(attrs={"class": base_input, "step": "0.01", "min": "0"}),
            "description": forms.Textarea(attrs={"class": f"{base_input} min-h-[100px]", "rows": 3}),
            "photo_url": forms.URLInput(attrs={"class": base_input, "placeholder": "https://..."}),
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
            "start_at": forms.DateTimeInput(attrs={"type": "datetime-local", "class": base_input, "required": True}),
            "end_at": forms.DateTimeInput(attrs={"type": "datetime-local", "class": base_input, "required": True}),
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
        return cleaned

    def save(self, commit=True):
        instance = super().save(commit=False)
        instance.is_confirmed = instance.status == "confirmed"
        if commit:
            instance.save()
            self.save_m2m()
        return instance


class BusinessUnitForm(forms.ModelForm):
    class Meta:
        model = BusinessUnit
        fields = ["name", "address", "description", "photo_url"]
        base_input = "w-full px-3 py-2 rounded-lg bg-panel border border-white/10 text-text placeholder-muted focus:outline-none focus:ring-2 focus:ring-accent"
        widgets = {
            "name": forms.TextInput(attrs={"class": base_input, "required": True}),
            "address": forms.TextInput(attrs={"class": base_input}),
            "description": forms.Textarea(attrs={"class": f"{base_input} min-h-[100px]", "rows": 3}),
            "photo_url": forms.URLInput(attrs={"class": base_input, "placeholder": "https://..."}),
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

