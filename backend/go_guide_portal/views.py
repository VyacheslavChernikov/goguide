import os
import hashlib
import io
import json
import csv
import uuid
from decimal import Decimal
from datetime import timedelta, datetime
from pathlib import Path

from django.contrib.auth.decorators import login_required
from django.contrib.auth import authenticate, login, update_session_auth_hash
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib import messages
from django.http import HttpResponse, JsonResponse
from django.utils import timezone
from django.db.models import Sum, Count, Q
from django.urls import reverse
from django.views.decorators.csrf import csrf_exempt
from dotenv import load_dotenv

from business_units.models import BusinessUnit, PayoutRequest
from services.models import Service
from appointments.models import Appointment
from go_guide_portal.models import BusinessUnitUser
from go_guide_portal.forms import (
    ServiceForm,
    AppointmentForm,
    BusinessUnitForm,
    AdminPasswordForm,
    GigaChatSettingsForm,
    PayoutRequestForm,
)
from go_guide_portal.navigation import get_ui_texts, get_dashboard_labels
from bot.gigachat_ai import ask_gigachat, get_gigachat_access_token

# Грузим .env из корня проекта и из backend (рядом с manage.py) — чтобы работало в обоих кейсах
PROJECT_ROOT = Path(__file__).resolve().parents[2]
BACKEND_ROOT = PROJECT_ROOT / "backend"
load_dotenv(PROJECT_ROOT / ".env", override=False)
load_dotenv(BACKEND_ROOT / ".env", override=False)


def login_view(request):
    if request.user.is_authenticated:
        return redirect("go_guide_dashboard")

    if request.method == "POST":
        username = request.POST.get("username", "").strip()
        password = request.POST.get("password", "")
        user = authenticate(request, username=username, password=password)
        if user:
            login(request, user)
            return redirect("go_guide_dashboard")
        messages.error(request, "Неверный логин или пароль.")

    return render(request, "go_guide_portal/login.html", {})


def _get_user_unit(user):
    if hasattr(user, "businessunituser"):
        return getattr(user.businessunituser, "business_unit", None)
    try:
        link = BusinessUnitUser.objects.get(user=user)
        return link.business_unit
    except BusinessUnitUser.DoesNotExist:
        return None


def _build_contacts_context(unit):
    contacts = []
    if unit.address:
        contacts.append(f"Адрес: {unit.address}")
    if getattr(unit, "phone", ""):
        contacts.append(f"Телефон: {unit.phone}")
    if getattr(unit, "email", ""):
        contacts.append(f"E-mail: {unit.email}")
    if getattr(unit, "website", ""):
        contacts.append(f"Сайт: {unit.website}")
    if getattr(unit, "socials", ""):
        contacts.append(f"Соцсети/ссылки: {unit.socials}")
    if not contacts:
        contacts.append("Контакты: не заданы (нет адреса/телефона в данных площадки).")
    return "Контакты площадки:\n" + "\n".join(f"- {c}" for c in contacts)


def _build_analytics_context(unit):
    """
    Сводка по услугам и бронированиям для отчётных вопросов.
    """
    # Услуги
    services = Service.objects.filter(business_unit=unit).order_by("title")
    services_lines = []
    for s in services:
        services_lines.append(
            f"- {s.title} | тип: {s.get_service_type_display() if hasattr(s, 'get_service_type_display') else s.service_type} | цена: {s.price or 0} | доступно: {'да' if s.is_available else 'нет'}"
        )
    services_block = "Услуги:\n" + ("\n".join(services_lines) if services_lines else "- нет данных")

    # Бронирования
    apps = Appointment.objects.filter(business_unit=unit)
    total = apps.count()
    confirmed = apps.filter(status="confirmed")
    cancelled = apps.filter(status="cancelled")
    pending = apps.filter(status="pending")
    revenue = confirmed.aggregate(total=Sum("total_price"))["total"] or 0
    avg_check = confirmed.aggregate(avg=Sum("total_price") / Count("id"))["avg"] if confirmed.exists() else 0
    upcoming = confirmed.filter(start_at__gte=timezone.now()).order_by("start_at")[:5]
    upcoming_lines = [
        f"- {a.client_name or 'Клиент'} | {a.service.title if a.service else 'услуга?'} | {a.start_at} - {a.end_at} | {a.total_price or 0}"
        for a in upcoming
    ]
    bookings_block = (
        "Бронирования:\n"
        f"- всего: {total}\n"
        f"- подтверждено: {confirmed.count()}\n"
        f"- в ожидании: {pending.count()}\n"
        f"- отменено: {cancelled.count()}\n"
        f"- выручка подтверждённых: {revenue}\n"
        f"- средний чек подтверждённых: {avg_check or 0}\n"
        "Ближайшие заезды:\n" + ("\n".join(upcoming_lines) if upcoming_lines else "- нет запланированных")
    )

    return services_block + "\n\n" + bookings_block


def _calculate_balance(unit):
    """
    Считаем доступный баланс по оплаченных бронированиям минус созданные/выплаченные выводы.
    """
    paid_total = Appointment.objects.filter(business_unit=unit, payment_status="paid").aggregate(total=Sum("total_price"))[
        "total"
    ] or Decimal("0")
    reserved = (
        PayoutRequest.objects.filter(business_unit=unit, status__in=["pending", "processing"]).aggregate(total=Sum("amount"))[
            "total"
        ]
        or Decimal("0")
    )
    paid_out = (
        PayoutRequest.objects.filter(business_unit=unit, status="paid").aggregate(total=Sum("amount"))["total"]
        or Decimal("0")
    )
    available = Decimal(paid_total) - Decimal(reserved) - Decimal(paid_out)
    return {
        "paid_total": Decimal(paid_total),
        "reserved": Decimal(reserved),
        "paid_out": Decimal(paid_out),
        "available": available,
    }


def _initiate_payout(payout: PayoutRequest, unit: BusinessUnit, webhook_url: str = None):
    """
    Заглушка/упрощённый запуск выплаты.
    Если провайдер не настроен — помечаем как pending/manual.
    Если выбрана mock — сразу считаем выплаченным.
    Для реальных провайдеров оставляем status=processing, ожидаем webhook.
    """
    provider = (unit.payout_provider or os.getenv("PAYOUT_PROVIDER") or "manual") if unit else "manual"
    payout.provider = provider
    payout.provider_payout_id = payout.provider_payout_id or f"{provider}-{payout.id}"

    meta = payout.meta or {}
    meta["provider"] = provider
    meta["mode"] = getattr(unit, "payout_mode", "test") if unit else "test"
    meta["webhook_url"] = webhook_url
    meta["config_present"] = bool(getattr(unit, "payout_provider_key", "") and getattr(unit, "payout_provider_secret", ""))

    if provider == "mock":
        payout.status = "paid"
        payout.processed_at = timezone.now()
        meta["note"] = "mock payout — помечено как выплаченное сразу"
    elif provider == "manual":
        payout.status = "pending"
        meta["note"] = "Ручной вывод — отметьте статус через вебхук или вручную"
    else:
        payout.status = "processing"
        meta["note"] = "Провайдер задан. Требуется реальный API-вызов + вебхук."

    payout.meta = meta
    payout.save()
    return payout


def _build_bookings_context(unit):
    """
    Краткая сводка по бронированиям для ответов ассистента.
    """
    apps = Appointment.objects.filter(business_unit=unit).order_by("-created_at")
    total = apps.count()
    confirmed = apps.filter(status="confirmed").count()
    pending = apps.filter(status="pending").count()
    cancelled = apps.filter(status="cancelled").count()
    today = apps.filter(start_at__date=timezone.now().date()).count()
    upcoming = apps.filter(start_at__gte=timezone.now()).order_by("start_at")[:3]
    upcoming_lines = [
        f"- {a.client_name or 'Клиент'} | {a.service.title if a.service else 'услуга?'} | {a.start_at} - {a.end_at} | статус: {a.get_status_display()} | сумма: {a.total_price or 0}"
        for a in upcoming
    ]
    last_bookings = apps.order_by("-created_at")[:5]
    last_lines = [
        f"- {a.client_name or 'Клиент'} | {a.service.title if a.service else 'услуга?'} | {a.start_at} - {a.end_at} | статус: {a.get_status_display()} | сумма: {a.total_price or 0}"
        for a in last_bookings
    ]
    lines = [
        f"Всего бронирований: {total} (подтверждено: {confirmed}, в ожидании: {pending}, отменено: {cancelled})",
        f"Бронирований сегодня: {today}",
        "Ближайшие заезды:" if upcoming_lines else "Ближайших заездов нет.",
        *(upcoming_lines if upcoming_lines else []),
        "Последние бронирования:" if last_lines else "Бронирования отсутствуют.",
        *(last_lines if last_lines else []),
    ]
    return "БРОНИРОВАНИЯ:\n" + "\n".join(lines)


def _build_profile_context(unit):
    profile_parts = []
    # режим и политики
    times = []
    if unit.working_hours_from and unit.working_hours_to:
        times.append(f"Работаем: {unit.working_hours_from}–{unit.working_hours_to}")
    checkinout = []
    if unit.checkin_time:
        checkinout.append(f"Чек-ин: {unit.checkin_time}")
    if unit.checkout_time:
        checkinout.append(f"Чек-аут: {unit.checkout_time}")
    if times:
        profile_parts.append("\n".join(times))
    if checkinout:
        profile_parts.append("\n".join(checkinout))

    short_fields = [
        ("Парковка", unit.parking_info),
        ("Wi‑Fi", unit.wifi_info),
        ("Питание", unit.meals_info),
        ("Детская политика", unit.kids_policy),
        ("Питомцы", unit.pets_policy),
        ("Курение", unit.smoke_policy),
        ("Доступность", unit.accessibility),
        ("Проезд/координаты", unit.coordinates),
    ]
    for label, val in short_fields:
        if val:
            profile_parts.append(f"{label}: {val}")

    if unit.positioning:
        profile_parts.append(f"УТП/позиционирование: {unit.positioning}")
    if unit.description:
        profile_parts.append(f"Описание: {unit.description}")

    if unit.tone:
        tone_map = {
            "friendly": "дружелюбный",
            "neutral": "нейтральный",
            "formal": "строгий",
        }
        profile_parts.append(f"Тон ассистента: {tone_map.get(unit.tone, unit.tone)}; эмодзи: {'да' if unit.allow_emoji else 'нет'}")

    if not profile_parts:
        return ""
    return "Профиль площадки:\n" + "\n".join(f"- {p}" for p in profile_parts)


def _build_faq(unit):
    def val(v, fallback="не указано"):
        return v if v else fallback

    faq_parts = [
        f"Чек-ин / чек-аут: {val(unit.checkin_time)} / {val(unit.checkout_time)}",
        f"Парковка: {val(unit.parking_info)}",
        f"Wi‑Fi: {val(unit.wifi_info)}",
        f"Питание: {val(unit.meals_info)}",
        f"Питомцы: {val(unit.pets_policy)}",
        f"Курение: {val(unit.smoke_policy)}",
        f"Дети: {val(unit.kids_policy)}",
        f"Доступность: {val(unit.accessibility)}",
        f"Адрес: {val(unit.address)}",
        f"Телефон: {val(getattr(unit, 'phone', ''))}",
        f"E-mail: {val(getattr(unit, 'email', ''))}",
        f"Сайт: {val(getattr(unit, 'website', ''))}",
    ]
    return "FAQ (быстрые ответы для гостей):\n" + "\n".join(f"- {p}" for p in faq_parts)


def _build_checklist(name: str):
    if name == "checkin":
        return (
            "Чек-лист заселения:\n"
            "- Проверить готовность номера (уборка, бельё, расходники)\n"
            "- Проверить документы гостя и оплату/депозит\n"
            "- Озвучить правила (чек-аут, курение, тишина, питомцы)\n"
            "- Выдать ключ/карту, показать Wi‑Fi, контакты ресепшн\n"
            "- Сообщить про завтрак/питание и время работы\n"
            "- Уточнить пожелания (детская кроватка, поздний выезд)\n"
        )
    if name == "event":
        return (
            "Чек-лист мероприятия:\n"
            "- Подтвердить дату/время и сценарий\n"
            "- Зал/площадка готова (рассадка, техника, климат)\n"
            "- Кофе-брейк/фуршет: время, меню, сервировка\n"
            "- Ответственные контакты: техподдержка, координатор\n"
            "- Навигация и указатели для гостей\n"
            "- План уборки и закрытия после мероприятия\n"
        )
    return ""


def _build_incident_playbook(kind: str):
    base = [
        "- Сохраняем спокойствие, уточняем детали, благодарим за сигнал.",
        "- Фиксируем время, номер/локацию, контакты гостя.",
        "- При необходимости — быстро уведомляем ответственного/дежурного.",
    ]
    if kind == "noise":
        extra = [
            "- Проверяем источник шума; предупреждение нарушителям, при повторе — эскалация.",
            "- Предлагаем гостю альтернативу: тихий номер/поздний check-out при возможности.",
        ]
    elif kind == "cleaning":
        extra = [
            "- Отправляем уборку/хозяйственную службу с приоритетом.",
            "- Проверяем расходники, бельё, запахи; фотоконтроль.",
        ]
    elif kind == "payment":
        extra = [
            "- Проверяем транзакцию/бронь; объясняем гостю статус.",
            "- Предлагаем безопасный способ оплаты; выдаём чек/квитанцию.",
        ]
    else:
        extra = [
            "- Определяем тип проблемы: шум/уборка/оплата/авария.",
            "- Если требуется эвакуация/аварийная служба — действуем по инструкции.",
        ]
    finish = [
        "- После решения: перезвонить гостю, подтвердить удовлетворённость.",
        "- Сделать запись в журнале/CRM для последующего анализа.",
    ]
    return "Инцидент — порядок действий:\n" + "\n".join(base + extra + finish)


def _build_guest_reply(unit):
    # Короткий шаблон ответа гостю с фактами из профиля
    def val(v, fallback="не указано"):
        return v if v else fallback

    parts = [
        "Здравствуйте! Спасибо за обращение.",
        f"Чек-ин: {val(unit.checkin_time)}, чек-аут: {val(unit.checkout_time)}.",
        f"Парковка: {val(unit.parking_info)}. Wi‑Fi: {val(unit.wifi_info)}.",
        f"Питание: {val(unit.meals_info)}.",
        f"Адрес: {val(unit.address)}. Телефон: {val(getattr(unit, 'phone', ''))}.",
    ]
    if getattr(unit, "email", ""):
        parts.append(f"Email: {unit.email}.")
    if getattr(unit, "website", ""):
        parts.append(f"Сайт: {unit.website}.")
    parts.append("Если потребуется помощь — мы рядом.")
    return "\n".join(parts)


def _quick_command_reply(user_msg: str, unit):
    text = user_msg.lower()
    if "faq" in text:
        return _build_faq(unit)
    if "чеклист" in text or "чек-лист" in text:
        if "засел" in text or "check-in" in text:
            return _build_checklist("checkin")
        if "меропр" in text or "event" in text or "ивент" in text:
            return _build_checklist("event")
    if "контакт" in text or "профиль" in text:
        return "\n\n".join(
            part for part in [_build_contacts_context(unit), _build_profile_context(unit)] if part
        )
    if "инцид" in text or "жалоб" in text or "эскалац" in text:
        if "шум" in text:
            return _build_incident_playbook("noise")
        if "уборк" in text or "чист" in text:
            return _build_incident_playbook("cleaning")
        if "оплат" in text or "платеж" in text or "чек" in text:
            return _build_incident_playbook("payment")
        return _build_incident_playbook("generic")
    if "ответ гостю" in text or "ответить гостю" in text or "guest" in text:
        return _build_guest_reply(unit)
    return None


def get_gigachat_auth_key(request):
    """
    Единый источник ключа: только переменная окружения.
    """
    return os.environ.get("GIGACHAT_BASIC_AUTH")


@login_required
def dashboard(request):
    unit = _get_user_unit(request.user)

    if not unit:
        return render(
            request,
            "go_guide_portal/dashboard.html",
            {"unit": None, "user_name": request.user.get_full_name() or request.user.username},
        )

    from django.db.models import Sum

    now = timezone.now()
    active_appointments = Appointment.objects.filter(
        business_unit=unit,
        status="confirmed",
        end_at__gte=now
    ).count()

    total_appointments = Appointment.objects.filter(business_unit=unit).count()

    total_revenue = Appointment.objects.filter(
        business_unit=unit,
        status="confirmed"
    ).aggregate(total=Sum('total_price'))['total'] or 0

    total_services = Service.objects.filter(business_unit=unit).count()

    recent_appointments = Appointment.objects.filter(business_unit=unit).order_by('-created_at')[:5]

    ui_texts = get_ui_texts(unit)
    dashboard_labels = get_dashboard_labels(ui_texts)

    context = {
        "unit": unit,
        "user_name": request.user.get_full_name() or request.user.username,
        "active_appointments": active_appointments,
        "total_appointments": total_appointments,
        "total_revenue": total_revenue,
        "total_services": total_services,
        "recent_appointments": recent_appointments,
        "occupancy_data": json.dumps([]),
        "unread_notifications": recent_appointments,
        "unread_count": recent_appointments.count(),
        "ui_texts": ui_texts,
        "dashboard_labels": dashboard_labels,
    }
    return render(request, "go_guide_portal/dashboard.html", context)


@login_required
def knowledge_upload(request):
    unit = _get_user_unit(request.user)
    if not unit:
        messages.error(request, "Вы не привязаны к площадке. Обратитесь к администратору.")
        return redirect("go_guide_dashboard")
    # Заглушка загрузки знаний (перенесём на Tailwind позже)
    return render(request, "go_guide_portal/knowledge_upload.html", {"unit": unit})


@login_required
def services_view(request):
    unit = _get_user_unit(request.user)
    if not unit:
        messages.error(request, "Вы не привязаны к площадке.")
        return redirect("go_guide_dashboard")
    ui_texts = get_ui_texts(unit)
    services = Service.objects.filter(business_unit=unit)
    form = ServiceForm()
    context = {
        "services": services,
        "unit": unit,
        "page_title": ui_texts.get("service_title", "Услуги"),
        "form": form,
        "service_types": Service.ROOM_TYPES,
        "ui_texts": ui_texts,
    }
    return render(request, "go_guide_portal/services.html", context)


@login_required
def service_create(request):
    unit = _get_user_unit(request.user)
    if not unit:
        messages.error(request, "Вы не привязаны к площадке.")
        return redirect("go_guide_dashboard")
    if request.method != "POST":
        return redirect("services")

    form = ServiceForm(request.POST)
    if form.is_valid():
        obj = form.save(commit=False)
        obj.business_unit = unit
        obj.save()
        messages.success(request, "Услуга создана.")
        if "save_add_another" in request.POST:
            return redirect("services")
    else:
        messages.error(request, "Исправьте ошибки формы.")
    return redirect("services")


@login_required
def service_update(request, pk):
    unit = _get_user_unit(request.user)
    if not unit:
        messages.error(request, "Вы не привязаны к площадке.")
        return redirect("go_guide_dashboard")
    service = get_object_or_404(Service, pk=pk, business_unit=unit)
    if request.method != "POST":
        return redirect("services")

    form = ServiceForm(request.POST, instance=service)
    if form.is_valid():
        form.save()
        messages.success(request, "Услуга обновлена.")
    else:
        messages.error(request, "Исправьте ошибки формы.")
    return redirect("services")


@login_required
def service_delete(request, pk):
    unit = _get_user_unit(request.user)
    if not unit:
        messages.error(request, "Вы не привязаны к площадке.")
        return redirect("go_guide_dashboard")
    service = get_object_or_404(Service, pk=pk, business_unit=unit)
    if request.method == "POST":
        service.delete()
        messages.success(request, "Услуга удалена.")
    return redirect("services")


@login_required
def service_duplicate(request, pk):
    unit = _get_user_unit(request.user)
    if not unit:
        messages.error(request, "Вы не привязаны к площадке.")
        return redirect("go_guide_dashboard")
    service = get_object_or_404(Service, pk=pk, business_unit=unit)
    if request.method != "POST":
        return redirect("services")
    dup = Service(
        business_unit=unit,
        title=f"{service.title} (копия)",
        service_type=service.service_type,
        price=service.price,
        description=service.description,
        is_available=service.is_available,
        photo_url=service.photo_url,
    )
    dup.save()
    messages.success(request, "Услуга продублирована.")
    return redirect("services")


@login_required
def rooms_view(request):
    """
    Для бизнес-типов hotel используем те же данные услуг, но показываем как "Номера".
    """
    unit = _get_user_unit(request.user)
    if not unit:
        messages.error(request, "Вы не привязаны к площадке.")
        return redirect("go_guide_dashboard")
    ui_texts = get_ui_texts(unit)
    services = Service.objects.filter(business_unit=unit)
    form = ServiceForm()
    context = {
        "services": services,
        "unit": unit,
        "page_title": ui_texts.get("service_title", "Номера"),
        "form": form,
        "service_types": Service.ROOM_TYPES,
        "ui_texts": ui_texts,
    }
    return render(request, "go_guide_portal/rooms.html", context)


@login_required
def room_create(request):
    unit = _get_user_unit(request.user)
    if not unit:
        messages.error(request, "Вы не привязаны к площадке.")
        return redirect("go_guide_dashboard")
    if request.method != "POST":
            return redirect("rooms")
    form = ServiceForm(request.POST)
    if form.is_valid():
        room = form.save(commit=False)
        room.business_unit = unit
        room.save()
        messages.success(request, "Номер создан.")
    else:
        messages.error(request, "Исправьте ошибки формы.")
    return redirect("rooms")


@login_required
def room_update(request, pk):
    unit = _get_user_unit(request.user)
    if not unit:
        messages.error(request, "Вы не привязаны к площадке.")
        return redirect("go_guide_dashboard")
    room = get_object_or_404(Service, pk=pk, business_unit=unit)
    if request.method != "POST":
        return redirect("rooms")
    form = ServiceForm(request.POST, instance=room)
    if form.is_valid():
        form.save()
        messages.success(request, "Номер обновлён.")
    else:
        messages.error(request, "Исправьте ошибки формы.")
    return redirect("rooms")


@login_required
def room_delete(request, pk):
    unit = _get_user_unit(request.user)
    if not unit:
        messages.error(request, "Вы не привязаны к площадке.")
        return redirect("go_guide_dashboard")
    room = get_object_or_404(Service, pk=pk, business_unit=unit)
    if request.method == "POST":
        room.delete()
        messages.success(request, "Номер удалён.")
    return redirect("rooms")


@login_required
def appointments_view(request):
    unit = _get_user_unit(request.user)
    if not unit:
        messages.error(request, "Вы не привязаны к площадке.")
        return redirect("go_guide_dashboard")
    ui_texts = get_ui_texts(unit)
    apps_qs = Appointment.objects.filter(business_unit=unit).order_by('-created_at')
    form = AppointmentForm(initial={
        "start_at": timezone.now(),
        "end_at": timezone.now() + timedelta(hours=1),
    })
    form.fields["service"].queryset = Service.objects.filter(business_unit=unit)
    context = {
        "appointments": apps_qs,
        "unit": unit,
        "page_title": ui_texts.get("booking_title", "Записи"),
        "service_label": ui_texts.get("service_singular", "Услуга"),
        "ui_texts": ui_texts,
        "form": form,
        "statuses": Appointment.STATUS_CHOICES,
    }
    return render(request, "go_guide_portal/appointments.html", context)


@login_required
def appointment_create(request):
    unit = _get_user_unit(request.user)
    if not unit:
        messages.error(request, "Вы не привязаны к площадке.")
        return redirect("go_guide_dashboard")
    if request.method != "POST":
        return redirect("appointments")

    form = AppointmentForm(request.POST)
    form.fields["service"].queryset = Service.objects.filter(business_unit=unit)
    if form.is_valid():
        obj = form.save(commit=False)
        obj.business_unit = unit
        pay_status = request.POST.get("payment_status") or obj.payment_status or "pending"
        obj.payment_status = pay_status
        if not obj.total_price and obj.service:
            obj.total_price = obj.service.price
        obj.is_confirmed = obj.status == "confirmed" or pay_status == "paid"
        obj.save()
        form.save_m2m()
        messages.success(request, "Запись создана.")
    else:
        non_field = form.non_field_errors()
        err_text = "; ".join(non_field) if non_field else form.errors.as_text()
        messages.error(request, f"Не удалось сохранить запись: {err_text}")
    return redirect("appointments")


@login_required
def appointment_update(request, pk):
    unit = _get_user_unit(request.user)
    if not unit:
        messages.error(request, "Вы не привязаны к площадке.")
        return redirect("go_guide_dashboard")
    appointment = get_object_or_404(Appointment, pk=pk, business_unit=unit)
    if request.method != "POST":
        return redirect("appointments")
    form = AppointmentForm(request.POST, instance=appointment)
    form.fields["service"].queryset = Service.objects.filter(business_unit=unit)
    if form.is_valid():
        obj = form.save(commit=False)
        obj.business_unit = unit
        pay_status = request.POST.get("payment_status") or obj.payment_status or "pending"
        obj.payment_status = pay_status
        obj.is_confirmed = obj.status == "confirmed" or pay_status == "paid"
        obj.save()
        form.save_m2m()
        messages.success(request, "Запись обновлена.")
    else:
        non_field = form.non_field_errors()
        err_text = "; ".join(non_field) if non_field else form.errors.as_text()
        messages.error(request, f"Не удалось обновить запись: {err_text}")
    return redirect("appointments")


@login_required
def appointment_delete(request, pk):
    unit = _get_user_unit(request.user)
    if not unit:
        messages.error(request, "Вы не привязаны к площадке.")
        return redirect("go_guide_dashboard")
    appointment = get_object_or_404(Appointment, pk=pk, business_unit=unit)
    if request.method == "POST":
        appointment.delete()
        messages.success(request, "Запись удалена.")
    return redirect("appointments")


@login_required
def appointments_export_csv(request):
    unit = _get_user_unit(request.user)
    if not unit:
        messages.error(request, "Вы не привязаны к площадке.")
        return redirect("go_guide_dashboard")

    queryset = Appointment.objects.filter(business_unit=unit).order_by('-created_at')
    status = request.GET.get("status")
    if status and status != "all":
        queryset = queryset.filter(status=status)

    response = HttpResponse(content_type="text/csv")
    response["Content-Disposition"] = 'attachment; filename="appointments.csv"'
    writer = csv.writer(response)
    writer.writerow(["ID", "Клиент", "Услуга", "Начало", "Окончание", "Сумма", "Статус"])
    for app in queryset:
        writer.writerow([
            app.id,
            app.client_name,
            app.service.title if app.service else "",
            app.start_at,
            app.end_at,
            app.total_price,
            app.get_status_display(),
        ])
    return response


@login_required
def bookings_view(request):
    """
    Алиас для hotel: показываем записи как бронирования.
    """
    unit = _get_user_unit(request.user)
    if not unit:
        messages.error(request, "Вы не привязаны к площадке.")
        return redirect("go_guide_dashboard")
    ui_texts = get_ui_texts(unit)
    queryset = Appointment.objects.filter(business_unit=unit).order_by('-created_at')

    status = request.GET.get("status", "all")
    # поддерживаем оба варианта имен параметров
    date_from = request.GET.get("start_date") or request.GET.get("date_from") or ""
    date_to = request.GET.get("end_date") or request.GET.get("date_to") or ""

    def _parse_date(value: str):
        if not value:
            return None
        for fmt in ("%Y-%m-%d", "%d.%m.%Y"):
            try:
                return datetime.strptime(value, fmt).date()
            except Exception:
                continue
        try:
            return datetime.fromisoformat(value).date()
        except Exception:
            return None

    if status and status != "all":
        queryset = queryset.filter(status=status)

    start_dt = _parse_date(date_from)
    end_dt = _parse_date(date_to)
    if start_dt:
        queryset = queryset.filter(start_at__date__gte=start_dt)
    if end_dt:
        queryset = queryset.filter(end_at__date__lte=end_dt)

    form = AppointmentForm(initial={
        "start_at": timezone.now(),
        "end_at": timezone.now() + timedelta(hours=2),
    })
    form.fields["service"].queryset = Service.objects.filter(business_unit=unit)

    context = {
        "appointments": queryset,
        "unit": unit,
        "page_title": ui_texts.get("booking_title", "Бронирования"),
        "service_label": ui_texts.get("service_singular", "Услуга"),
        "form": form,
        "statuses": Appointment.STATUS_CHOICES,
        "current_status": status,
        "date_from": date_from,
        "date_to": date_to,
        "ui_texts": ui_texts,
    }
    return render(request, "go_guide_portal/bookings.html", context)


@login_required
def booking_create(request):
    unit = _get_user_unit(request.user)
    if not unit:
        messages.error(request, "Вы не привязаны к площадке.")
        return redirect("go_guide_dashboard")
    if request.method != "POST":
        return redirect("bookings")

    form = AppointmentForm(request.POST)
    form.fields["service"].queryset = Service.objects.filter(business_unit=unit)
    if form.is_valid():
        booking = form.save(commit=False)
        booking.business_unit = unit
        booking.payment_status = request.POST.get("payment_status") or "pending"
        # если цена не указана — подставим цену услуги
        if not booking.total_price and booking.service:
            booking.total_price = booking.service.price
        booking.is_confirmed = booking.status == "confirmed" or booking.payment_status == "paid"
        booking.save()
        form.save_m2m()
        messages.success(request, "Бронирование создано.")
    else:
        messages.error(request, "Исправьте ошибки формы.")
    return redirect("bookings")


@login_required
def booking_update(request, pk):
    unit = _get_user_unit(request.user)
    if not unit:
        messages.error(request, "Вы не привязаны к площадке.")
        return redirect("go_guide_dashboard")
    booking = get_object_or_404(Appointment, pk=pk, business_unit=unit)
    if request.method != "POST":
        return redirect("bookings")
    form = AppointmentForm(request.POST, instance=booking)
    form.fields["service"].queryset = Service.objects.filter(business_unit=unit)
    if form.is_valid():
        obj = form.save(commit=False)
        obj.business_unit = unit
        obj.payment_status = request.POST.get("payment_status") or obj.payment_status or "pending"
        obj.is_confirmed = obj.status == "confirmed" or obj.payment_status == "paid"
        obj.save()
        form.save_m2m()
        messages.success(request, "Бронирование обновлено.")
    else:
        messages.error(request, f"Исправьте ошибки формы: {form.errors.as_text()}")
    return redirect("bookings")


@login_required
def booking_delete(request, pk):
    unit = _get_user_unit(request.user)
    if not unit:
        messages.error(request, "Вы не привязаны к площадке.")
        return redirect("go_guide_dashboard")
    booking = get_object_or_404(Appointment, pk=pk, business_unit=unit)
    if request.method == "POST":
        booking.delete()
        messages.success(request, "Бронирование удалено.")
    return redirect("bookings")


@login_required
def bookings_export_csv(request):
    unit = _get_user_unit(request.user)
    if not unit:
        messages.error(request, "Вы не привязаны к площадке.")
        return redirect("go_guide_dashboard")

    queryset = Appointment.objects.filter(business_unit=unit).order_by('-created_at')
    status = request.GET.get("status")
    if status and status != "all":
        queryset = queryset.filter(status=status)

    response = HttpResponse(content_type="text/csv")
    response["Content-Disposition"] = 'attachment; filename="bookings.csv"'
    writer = csv.writer(response)
    writer.writerow(["ID", "Клиент", "Услуга", "Начало", "Окончание", "Сумма", "Статус"])
    for app in queryset:
        writer.writerow([
            app.id,
            app.client_name,
            app.service.title if app.service else "",
            app.start_at,
            app.end_at,
            app.total_price,
            app.get_status_display(),
        ])
    return response


@login_required
def ai_assistant_view(request):
    unit = _get_user_unit(request.user)
    if not unit:
        messages.error(request, "Вы не привязаны к площадке.")
        return redirect("go_guide_dashboard")
    ui_texts = get_ui_texts(unit)

    # сохранение ключей
    if request.method == "POST" and "save_ai" in request.POST:
        gigachat_key = request.POST.get("gigachat_auth_key", "").strip()
        alice_key = request.POST.get("alice_key", "").strip()
        if gigachat_key:
            unit.gigachat_auth_key = gigachat_key
        if alice_key:
            unit.alice_key = alice_key
        unit.save(update_fields=["gigachat_auth_key", "alice_key"])
        messages.success(request, "Настройки AI сохранены.")
        return redirect("ai_assistant")

    # чат (история для отображения — наполняется в chat_with_ai)
    chat_history = request.session.get("ai_chat_history", [])

    context = {
        "unit": unit,
        "gigachat_key": unit.gigachat_auth_key or unit.gigachat_key or "",
        "alice_key": unit.alice_key or "",
        "chat_history": chat_history,
        "ui_texts": ui_texts,
    }
    return render(request, "go_guide_portal/ai_assistant.html", context)


@login_required
def chat_with_ai(request):
    if request.method != "POST":
        return JsonResponse({"error": "METHOD_NOT_ALLOWED"}, status=405)

    unit = _get_user_unit(request.user)
    if not unit:
        return JsonResponse({"error": "NO_UNIT", "message": "Вы не привязаны к площадке."}, status=400)

    user_msg = (request.POST.get("chat_message") or "").strip()
    if not user_msg:
        return JsonResponse({"error": "EMPTY_MESSAGE", "message": "Введите вопрос."}, status=400)

    quick_reply = _quick_command_reply(user_msg, unit)
    if quick_reply:
        chat_history = request.session.get("ai_chat_history", [])
        chat_history.append({"role": "user", "content": user_msg})
        chat_history.append({"role": "assistant", "content": quick_reply})
        request.session["ai_chat_history"] = chat_history
        request.session.modified = True
        return JsonResponse({"reply": quick_reply})

    if not unit.gigachat_auth_key:
        return JsonResponse(
            {
                "error": "GIGACHAT_NOT_CONFIGURED",
                "message": "Заполни GigaChat Authorization key в /dashboard/integrations/gigachat/",
            },
            status=400,
        )

    context_text = ""

    lowered = user_msg.lower()
    analytics_needed = any(
        kw in lowered
        for kw in ["аналит", "отчет", "отчёт", "statistics", "report", "метрик", "показател", "статист"]
    )
    marketing_needed = any(
        kw in lowered
        for kw in ["коммерческое предложение", "ком предложение", "презента", "реклама", "менеджер", "продаж", "предложение клиенту"]
    )
    bookings_needed = any(
        kw in lowered
        for kw in ["бронь", "брониров", "booking", "reservation", "засел", "отмена", "подтверд"]
    )
    analytics_block = _build_analytics_context(unit) if analytics_needed else ""
    bookings_block = _build_bookings_context(unit)

    contacts_block = _build_contacts_context(unit)
    profile_block = _build_profile_context(unit)

    if analytics_needed:
        combined_context = "\n\n".join([part for part in [contacts_block, profile_block, analytics_block, bookings_block] if part.strip()])
    elif bookings_needed:
        combined_context = "\n\n".join([part for part in [contacts_block, profile_block, bookings_block] if part.strip()])
    elif marketing_needed:
        combined_context = "\n\n".join([part for part in [contacts_block, profile_block, bookings_block] if part.strip()])
    else:
        # базовый ответ: контакты, профиль, краткие брони
        combined_context = "\n\n".join([part for part in [contacts_block, profile_block, bookings_block] if part.strip()])

    if not combined_context:
        return JsonResponse({"error": "NO_CONTEXT", "message": "Не найден контекст для ответа (профиль не заполнен)."}, status=400)

    prompt_parts = [
        "Отвечай только на основе приведённого контекста.",
        "Если ответа нет в контексте, скажи, что данных недостаточно.",
        "Форматируй ответ простым текстом: без Markdown, без символов #, **, |.",
        "Используй читаемые блоки с заголовками в верхнем регистре и короткими пунктами с тире.",
        "Не используй таблицы и вертикальные разделители, только строки с переносами.",
    ]
    if analytics_needed:
        prompt_parts.append(
            "Для отчётов используй блок АНАЛИТИКА с метриками и при наличии — БЛИЖАЙШИЕ ЗАЕЗДЫ, каждый пункт с тире."
        )
    if marketing_needed:
        prompt_parts.append(
            "Сделай короткое коммерческое предложение на основе фактов из контекста: Заголовок, Контакты, Преимущества/особенности, Услуги и ориентиры по цене (если есть в контексте), Призыв связаться. "
            "Пиши связанным текстом, не копируй дословно весь контекст, выделяй главное. Можно добавить 1-3 уместных эмодзи, но не злоупотребляй."
        )
    prompt_parts.append(f"Контекст:\n{combined_context}\n\nВопрос: {user_msg}\nОтвет:")
    prompt = " ".join(prompt_parts)
    print("[CHAT] prompt composed, context length:", len(combined_context))

    try:
        reply = ask_gigachat(
            prompt,
            auth_key=unit.gigachat_auth_key,
            client_id=unit.gigachat_client_id,
            chat_url=None,
            scope=unit.gigachat_scope or None,
        )
    except Exception as exc:
        fallback = (
            "Ассистент временно недоступен (ошибка подключения к GigaChat). "
            "Проверьте ключи/подключение и попробуйте позже. "
            f"Техническая ошибка: {exc}"
        )
        # сохраняем в историю, чтобы пользователь видел сообщение
        chat_history = request.session.get("ai_chat_history", [])
        chat_history.append({"role": "user", "content": user_msg})
        chat_history.append({"role": "assistant", "content": fallback})
        request.session["ai_chat_history"] = chat_history
        request.session.modified = True
        return JsonResponse({"reply": fallback, "error": "GIGACHAT_API_ERROR", "message": str(exc)}, status=200)

    chat_history = request.session.get("ai_chat_history", [])
    chat_history.append({"role": "user", "content": user_msg})
    chat_history.append({"role": "assistant", "content": reply})
    request.session["ai_chat_history"] = chat_history
    request.session.modified = True

    return JsonResponse({"reply": reply})


@login_required
def gigachat_settings_view(request):
    unit = _get_user_unit(request.user)
    if not unit:
        # временный fallback — берём первую площадку
        unit = BusinessUnit.objects.first()
        if not unit:
            messages.error(request, "Нет площадок для настройки GigaChat.")
            return redirect("go_guide_dashboard")

    form = GigaChatSettingsForm(instance=unit)

    if request.method == "POST":
        form = GigaChatSettingsForm(request.POST, instance=unit)
        if form.is_valid():
            prev_auth = unit.gigachat_auth_key
            prev_scope = unit.gigachat_scope or "GIGACHAT_API_PERS"
            prev_client = unit.gigachat_client_id

            raw_auth = (form.cleaned_data.get("gigachat_auth_key") or "").strip()
            raw_scope = (form.cleaned_data.get("gigachat_scope") or "").strip()
            raw_client = (form.cleaned_data.get("gigachat_client_id") or "").strip()

            # Берём введённые значения, иначе — ранее сохранённые
            auth_val = raw_auth if raw_auth else prev_auth
            scope_val = raw_scope if raw_scope else prev_scope
            client_val = raw_client if len(raw_client) >= 10 else prev_client

            if not auth_val:
                messages.error(request, "Заполните Authorization key.")
                return redirect("gigachat_settings")
            if not client_val:
                messages.error(request, "Заполните Client ID.")
                return redirect("gigachat_settings")

            obj = form.save(commit=False)
            obj.gigachat_auth_key = auth_val
            obj.gigachat_scope = scope_val
            obj.gigachat_client_id = client_val
            obj.save()
            print(
                "[GIGACHAT SETTINGS] saved:",
                "client_id len:", len(obj.gigachat_client_id or "0"),
                "auth len:", len(obj.gigachat_auth_key or "0"),
                "scope:", obj.gigachat_scope,
            )
            if "save" in request.POST and "test_connection" not in request.POST:
                messages.success(request, "GigaChat ключи сохранены.")
        else:
            messages.error(request, "Исправьте ошибки формы.")

        # Проверка подключения (после сохранения, если нужно)
        if "test_connection" in request.POST:
            unit.refresh_from_db()
            auth_used = unit.gigachat_auth_key
            scope_used = unit.gigachat_scope or "GIGACHAT_API_PERS"
            client_used = unit.gigachat_client_id
            print("[GIGACHAT TEST] start check, client_id len:", len(client_used or "0"), "auth len:", len(auth_used or "0"), "scope:", scope_used)
            try:
                token = get_gigachat_access_token(
                    auth_key=auth_used,
                    scope=scope_used,
                    force_refresh=True,
                )
                print("[GIGACHAT TEST] token obtained, len:", len(token or ""))
                messages.success(request, "Подключение успешно, токен получен.")
            except Exception as exc:
                print("[GIGACHAT TEST] error:", exc)
                messages.error(request, f"Ошибка подключения: {exc}")
            return redirect("gigachat_settings")

        return redirect("gigachat_settings")

    return render(
        request,
        "go_guide_portal/gigachat_settings.html",
        {
            "unit": unit,
            "form": form,
        },
    )

@login_required
def analytics_view(request):
    unit = _get_user_unit(request.user)
    if not unit:
        messages.error(request, "Вы не привязаны к площадке.")
        return redirect("go_guide_dashboard")
    ui_texts = get_ui_texts(unit)

    bookings = Appointment.objects.filter(business_unit=unit)
    confirmed = bookings.filter(status="confirmed")
    now = timezone.now()

    total_bookings = bookings.count()
    active_bookings = confirmed.filter(end_at__gte=now).count()
    total_revenue = confirmed.aggregate(total=Sum("total_price"))["total"] or 0

    rooms_count = Service.objects.filter(business_unit=unit).count()
    occupancy_rate = 0
    if rooms_count:
        occupancy_rate = min(active_bookings, rooms_count) / rooms_count * 100

    # Revenue by month (last 6 months)
    revenue_chart = []
    today = timezone.now().date().replace(day=1)
    for i in range(5, -1, -1):
        month_start = (today - timedelta(days=30 * i)).replace(day=1)
        next_month = (month_start + timedelta(days=32)).replace(day=1)
        value = confirmed.filter(
            created_at__date__gte=month_start,
            created_at__date__lt=next_month
        ).aggregate(total=Sum("total_price"))["total"] or 0
        revenue_chart.append({"label": month_start.strftime("%b %Y"), "value": float(value)})

    # Occupancy by weekday (count of confirmed bookings per weekday)
    weekday_stats = [0] * 7
    for b in confirmed:
        weekday_stats[b.start_at.weekday()] += 1

    # Top rooms
    top_rooms = (
        Service.objects.filter(business_unit=unit)
        .annotate(
            bookings_count=Count("appointment", filter=Q(appointment__status="confirmed")),
            revenue=Sum("appointment__total_price", filter=Q(appointment__status="confirmed")),
        )
        .order_by("-bookings_count", "-revenue")[:5]
    )

    context = {
        "unit": unit,
        "total_bookings": total_bookings,
        "active_bookings": active_bookings,
        "total_revenue": total_revenue,
        "occupancy_rate": round(occupancy_rate, 1) if occupancy_rate else 0,
        "revenue_chart": json.dumps(revenue_chart),
        "weekday_stats": weekday_stats,
        "top_rooms": top_rooms,
        "ui_texts": ui_texts,
    }
    return render(request, "go_guide_portal/analytics.html", context)


@login_required
def settings_view(request):
    unit = _get_user_unit(request.user)
    if not unit:
        messages.error(request, "Вы не привязаны к площадке.")
        return redirect("go_guide_dashboard")

    unit_form = BusinessUnitForm(instance=unit)
    pwd_form = AdminPasswordForm(user=request.user)
    payout_form = PayoutRequestForm()

    # embed code for booking widget
    base_url = request.build_absolute_uri("/").rstrip("/")
    webhook_url = request.build_absolute_uri(reverse("payout_webhook"))
    embed_code = (
        f'<script src="{base_url}/static/widget/booking-widget.js" defer></script>\n'
        f'<booking-widget data-bu-id="{unit.id}" data-api-base="{base_url}/api"></booking-widget>'
    )

    payouts = PayoutRequest.objects.filter(business_unit=unit).order_by("-created_at")[:20]
    balance = _calculate_balance(unit)
    payout_provider = os.getenv("PAYOUT_PROVIDER", "manual") or "manual"
    payout_provider = unit.payout_provider or payout_provider

    if request.method == "POST":
        if "create_payout" in request.POST:
            payout_form = PayoutRequestForm(request.POST)
            if payout_form.is_valid():
                payout = payout_form.save(commit=False)
                payout.business_unit = unit
                payout.currency = "RUB"
                payout.requested_by = request.user
                available = _calculate_balance(unit)["available"]
                if payout.amount and Decimal(payout.amount) > available:
                    messages.error(request, "Недостаточно средств для вывода.")
                    return redirect("settings")
                payout.save()
                _initiate_payout(payout, unit, webhook_url=webhook_url)
                messages.success(request, f"Заявка на выплату создана: {payout.amount} {payout.currency}.")
            else:
                messages.error(request, "Исправьте ошибки в форме вывода.")
        elif "create_test_payout" in request.POST:
            payout = PayoutRequest.objects.create(
                business_unit=unit,
                amount=Decimal("1.00"),
                fee=Decimal("0"),
                currency="RUB",
                requested_by=request.user,
                comment="Тестовая выплата",
            )
            _initiate_payout(payout, unit, webhook_url=webhook_url)
            messages.success(request, "Тестовая выплата создана (mock/processing). Проверьте статус ниже или по вебхуку.")
        elif "save_unit" in request.POST:
            unit_form = BusinessUnitForm(request.POST, instance=unit)
            if unit_form.is_valid():
                unit_form.save()
                messages.success(request, "Данные площадки сохранены.")
                return redirect("settings")
            else:
                messages.error(request, "Исправьте ошибки в форме площадки.")
        elif "change_password" in request.POST:
            pwd_form = AdminPasswordForm(user=request.user, data=request.POST)
            if pwd_form.is_valid():
                user = pwd_form.save()
                update_session_auth_hash(request, user)
                messages.success(request, "Пароль обновлён.")
            else:
                messages.error(request, "Не удалось сменить пароль.")
        return redirect("settings")

    context = {
        'unit': unit,
        'unit_form': unit_form,
        'pwd_form': pwd_form,
        'embed_code': embed_code,
        'payout_form': payout_form,
        'payouts': payouts,
        'balance': balance,
        'payout_provider': payout_provider,
        'webhook_url': webhook_url,
    }
    return render(request, "go_guide_portal/settings.html", context)


@login_required
def tours_view(request):
    unit = _get_user_unit(request.user)
    if not unit:
        messages.error(request, "Вы не привязаны к площадке.")
        return redirect("go_guide_dashboard")
    ui_texts = get_ui_texts(unit)

    tours = request.session.get('tours', [])

    if request.method == "POST":
        name = request.POST.get('name')
        url = request.POST.get('url')

        if name and url:
            tours.insert(0, {"name": name, "url": url})
            request.session['tours'] = tours
            messages.success(request, "Тур добавлен (сеанс).")
            return redirect("tours")
        else:
            messages.error(request, "Заполните все поля.")

    context = {
        'unit': unit,
        'tours': tours,
        'ui_texts': ui_texts,
        'page_title': ui_texts.get("service_title", "Туры"),
    }
    return render(request, "go_guide_portal/tours.html", context)


@csrf_exempt
def payout_webhook(request):
    """
    Приём вебхуков от провайдера выплат.
    Ожидаем JSON с полями payout_id (или id/provider_payout_id) и status.
    """
    if request.method != "POST":
        return JsonResponse({"error": "method not allowed"}, status=405)

    try:
        payload = json.loads(request.body.decode("utf-8"))
    except Exception:
        return JsonResponse({"error": "invalid json"}, status=400)

    payout_id = payload.get("payout_id") or payload.get("id") or payload.get("provider_payout_id")
    new_status = payload.get("status")

    if not payout_id or not new_status:
        return JsonResponse({"error": "payout_id and status are required"}, status=400)

    try:
        payout = PayoutRequest.objects.get(provider_payout_id=payout_id)
    except PayoutRequest.DoesNotExist:
        return JsonResponse({"error": "payout not found"}, status=404)

    status_map = {
        "succeeded": "paid",
        "paid": "paid",
        "processing": "processing",
        "pending": "pending",
        "canceled": "failed",
        "cancelled": "failed",
        "failed": "failed",
        "error": "failed",
    }
    mapped = status_map.get(new_status.lower(), None if not isinstance(new_status, str) else new_status.lower())
    if mapped in dict(PayoutRequest.STATUS_CHOICES):
        payout.status = mapped
        if mapped == "paid":
            payout.processed_at = timezone.now()

    meta = payout.meta or {}
    meta["webhook"] = payload
    payout.meta = meta
    payout.save(update_fields=["status", "processed_at", "meta"])

    return JsonResponse({"ok": True})

