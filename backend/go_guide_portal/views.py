import os
import hashlib
import io
import json
import csv
from datetime import timedelta, datetime
from pathlib import Path

from django.contrib.auth.decorators import login_required
from django.contrib.auth import authenticate, login, update_session_auth_hash
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib import messages
from django.http import HttpResponse, JsonResponse
from django.utils import timezone
from django.db.models import Sum, Count, Q
from dotenv import load_dotenv

from business_units.models import BusinessUnit
from services.models import Service
from appointments.models import Appointment
from go_guide_portal.models import BusinessUnitUser, KnowledgeFile, KnowledgeDocument
from go_guide_portal.forms import (
    ServiceForm,
    AppointmentForm,
    BusinessUnitForm,
    AdminPasswordForm,
    GigaChatSettingsForm,
)
from bot.gigachat_ai import ask_gigachat, get_gigachat_access_token

# Грузим .env из корня проекта и из backend (рядом с manage.py) — чтобы работало в обоих кейсах
PROJECT_ROOT = Path(__file__).resolve().parents[2]
BACKEND_ROOT = PROJECT_ROOT / "backend"
load_dotenv(PROJECT_ROOT / ".env", override=False)
load_dotenv(BACKEND_ROOT / ".env", override=False)

import chromadb

try:
    import PyPDF2
except ImportError:
    PyPDF2 = None


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
    }
    return render(request, "go_guide_portal/dashboard.html", context)


def _chunk_text(text, chunk_size=500, overlap=50):
    chunks = []
    start = 0
    length = len(text)
    while start < length:
        end = min(start + chunk_size, length)
        chunks.append(text[start:end])
        start += chunk_size - overlap
    return [c.strip() for c in chunks if c.strip()]


def _read_text_from_file(fobj, name):
    lower = name.lower()
    if lower.endswith(".txt"):
        return fobj.read().decode("utf-8", errors="ignore")
    if lower.endswith(".pdf"):
        if not PyPDF2:
            raise ValueError("Поддержка PDF не установлена (PyPDF2).")
        reader = PyPDF2.PdfReader(fobj)
        pages = []
        for page in reader.pages:
            pages.append(page.extract_text() or "")
        return "\n".join(pages)
    raise ValueError("Поддерживаются только TXT или PDF.")


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
    services = Service.objects.filter(business_unit=unit)
    form = ServiceForm()
    context = {
        "services": services,
        "unit": unit,
        "page_title": "Услуги",
        "form": form,
        "service_types": Service.ROOM_TYPES,
    }
    return render(request, "go_guide_portal/services.html", context)


@login_required
def rooms_view(request):
    """
    Для бизнес-типов hotel используем те же данные услуг, но показываем как "Номера".
    """
    unit = _get_user_unit(request.user)
    if not unit:
        messages.error(request, "Вы не привязаны к площадке.")
        return redirect("go_guide_dashboard")
    services = Service.objects.filter(business_unit=unit)
    form = ServiceForm()
    context = {
        "services": services,
        "unit": unit,
        "page_title": "Номера",
        "form": form,
        "service_types": Service.ROOM_TYPES,
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
    apps_qs = Appointment.objects.filter(business_unit=unit).order_by('-created_at')
    context = {
        "appointments": apps_qs,
        "unit": unit,
        "page_title": "Записи",
    }
    return render(request, "go_guide_portal/appointments.html", context)


@login_required
def bookings_view(request):
    """
    Алиас для hotel: показываем записи как бронирования.
    """
    unit = _get_user_unit(request.user)
    if not unit:
        messages.error(request, "Вы не привязаны к площадке.")
        return redirect("go_guide_dashboard")
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
        "page_title": "Бронирования",
        "form": form,
        "statuses": Appointment.STATUS_CHOICES,
        "current_status": status,
        "date_from": date_from,
        "date_to": date_to,
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
        # если цена не указана — подставим цену услуги
        if not booking.total_price and booking.service:
            booking.total_price = booking.service.price
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
        obj.is_confirmed = obj.status == "confirmed"
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

    # загрузка файла знаний
    if request.method == "POST" and "upload_knowledge" in request.POST:
        upload = request.FILES.get("knowledge_file")
        if upload and upload.name.lower().endswith(".txt"):
            doc = KnowledgeDocument.objects.create(
                business_unit=unit,
                file=upload,
                original_name=upload.name,
                status="pending",
            )
            messages.success(request, f"Файл {upload.name} загружен, ожидает обработки.")
        else:
            messages.error(request, "Загрузите .txt файл.")
        return redirect("ai_assistant")

    # чат
    chat_history = request.session.get("ai_chat_history", [])
    if request.method == "POST" and "chat_message_flag" in request.POST:
        user_msg = request.POST.get("chat_message", "").strip()
        if user_msg:
            chat_history.append({"role": "user", "content": user_msg})
            if not unit.gigachat_auth_key:
                return JsonResponse(
                    {
                        "error": "GIGACHAT_NOT_CONFIGURED",
                        "message": "Заполни GigaChat Authorization key в /dashboard/integrations/gigachat/",
                    },
                    status=400,
                )
            try:
                reply = ask_gigachat(
                    user_msg,
                    auth_key=unit.gigachat_auth_key,
                    client_id=unit.gigachat_client_id,
                    chat_url=None,
                    scope=unit.gigachat_scope or None,
                )
            except RuntimeError as exc:
                return JsonResponse({"error": "GIGACHAT_API_ERROR", "message": str(exc)}, status=502)
            chat_history.append({"role": "assistant", "content": reply})
            request.session["ai_chat_history"] = chat_history
            request.session.modified = True
            # если ajax-запрос — отдаем json, без редиректа и перерендера страницы
            if request.headers.get("x-requested-with") == "XMLHttpRequest":
                return JsonResponse({"reply": reply})
            return redirect("ai_assistant")

    knowledge_docs = KnowledgeDocument.objects.filter(business_unit=unit).order_by("-uploaded_at")

    context = {
        "unit": unit,
        "gigachat_key": unit.gigachat_auth_key or unit.gigachat_key or "",
        "alice_key": unit.alice_key or "",
        "knowledge_docs": knowledge_docs,
        "chat_history": chat_history,
    }
    return render(request, "go_guide_portal/ai_assistant.html", context)


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

    if request.method == "POST":
        if "save_unit" in request.POST:
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
                return redirect("settings")
            else:
                messages.error(request, "Не удалось сменить пароль.")

    context = {
        'unit': unit,
        'unit_form': unit_form,
        'pwd_form': pwd_form,
    }
    return render(request, "go_guide_portal/settings.html", context)


@login_required
def tours_view(request):
    unit = _get_user_unit(request.user)
    if not unit:
        messages.error(request, "Вы не привязаны к площадке.")
        return redirect("go_guide_dashboard")

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
    }
    return render(request, "go_guide_portal/tours.html", context)

