"""
Helpers for building navigation and UI labels per business type.
This keeps templates/views clean and centralizes wording/icons.
"""

ICON_HOME = """<svg class="w-5 h-5 mr-3" fill="none" stroke="currentColor" stroke-width="1.8" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" d="M3 12l9-8 9 8M4 10v10h6V14h4v6h6V10"/></svg>"""
ICON_ROOMS = """<svg class="w-5 h-5 mr-3" fill="none" stroke="currentColor" stroke-width="1.8" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" d="M4 10h16M4 14h16M10 6h4m-7 0h1m8 0h1M5 18h14"/></svg>"""
ICON_BOOKINGS = """<svg class="w-5 h-5 mr-3" fill="none" stroke="currentColor" stroke-width="1.8" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" d="M8 7V5a2 2 0 012-2h4a2 2 0 012 2v2m-8 0h8m-8 0H7a2 2 0 00-2 2v8a2 2 0 002 2h10a2 2 0 002-2V9a2 2 0 00-2-2h-1m-8 4h8m-8 4h5"/></svg>"""
ICON_ANALYTICS = """<svg class="w-5 h-5 mr-3" fill="none" stroke="currentColor" stroke-width="1.8" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" d="M4 19h16M7 16v-4m5 4V8m5 8V6"/></svg>"""
ICON_AI = """<svg class="w-5 h-5 mr-3" fill="none" stroke="currentColor" stroke-width="1.8" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" d="M12 6v6l4 2"/><circle cx="12" cy="12" r="9"/></svg>"""
ICON_SETTINGS = """<svg class="w-5 h-5 mr-3" fill="none" stroke="currentColor" stroke-width="1.8" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" d="M10.325 4.317l.675-1.842a1 1 0 011.9 0l.675 1.842a1 1 0 00.95.69h1.95a1 1 0 01.96 1.28l-.6 1.802a1 1 0 00.27 1.02l1.389 1.389a1 1 0 010 1.414l-1.389 1.389a1 1 0 00-.27 1.02l.6 1.802a1 1 0 01-.96 1.28h-1.95a1 1 0 00-.95.69l-.675 1.842a1 1 0 01-1.9 0l-.675-1.842a1 1 0 00-.95-.69h-1.95a1 1 0 01-.96-1.28l.6-1.802a1 1 0 00-.27-1.02L5.636 13.41a1 1 0 010-1.414l1.389-1.389a1 1 0 00.27-1.02l-.6-1.802A1 1 0 016.655 5h1.95a1 1 0 00.95-.683z"/><circle cx="12" cy="12" r="3"/></svg>"""
ICON_SERVICES = """<svg class="w-5 h-5 mr-3" fill="none" stroke="currentColor" stroke-width="1.8" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" d="M4 7h16M4 12h16M4 17h16"/></svg>"""

NAV_BY_TYPE = {
    "hotel": [
        {"url_name": "go_guide_dashboard", "label": "Главная", "icon": ICON_HOME},
        {"url_name": "rooms", "label": "Номера", "icon": ICON_ROOMS},
        {"url_name": "bookings", "label": "Бронирования", "icon": ICON_BOOKINGS},
        {"url_name": "analytics", "label": "Аналитика", "icon": ICON_ANALYTICS},
        {"url_name": "ai_assistant", "label": "AI-ассистент", "icon": ICON_AI},
        {"url_name": "settings", "label": "Настройки", "icon": ICON_SETTINGS},
    ],
    "service": [
        {"url_name": "go_guide_dashboard", "label": "Главная", "icon": ICON_HOME},
        {"url_name": "services", "label": "Услуги", "icon": ICON_SERVICES},
        {"url_name": "appointments", "label": "Записи", "icon": ICON_BOOKINGS},
        {"url_name": "analytics", "label": "Аналитика", "icon": ICON_ANALYTICS},
        {"url_name": "ai_assistant", "label": "AI-ассистент", "icon": ICON_AI},
        {"url_name": "settings", "label": "Настройки", "icon": ICON_SETTINGS},
    ],
    "tour": [
        {"url_name": "go_guide_dashboard", "label": "Главная", "icon": ICON_HOME},
        {"url_name": "tours", "label": "Туры/экскурсии", "icon": ICON_SERVICES},
        {"url_name": "bookings", "label": "Бронирования", "icon": ICON_BOOKINGS},
        {"url_name": "analytics", "label": "Аналитика", "icon": ICON_ANALYTICS},
        {"url_name": "ai_assistant", "label": "AI-ассистент", "icon": ICON_AI},
        {"url_name": "settings", "label": "Настройки", "icon": ICON_SETTINGS},
    ],
    "event": [
        {"url_name": "go_guide_dashboard", "label": "Главная", "icon": ICON_HOME},
        {"url_name": "tours", "label": "Мероприятия", "icon": ICON_SERVICES},
        {"url_name": "bookings", "label": "Билеты/брони", "icon": ICON_BOOKINGS},
        {"url_name": "analytics", "label": "Аналитика", "icon": ICON_ANALYTICS},
        {"url_name": "ai_assistant", "label": "AI-ассистент", "icon": ICON_AI},
        {"url_name": "settings", "label": "Настройки", "icon": ICON_SETTINGS},
    ],
    "rent": [
        {"url_name": "go_guide_dashboard", "label": "Главная", "icon": ICON_HOME},
        {"url_name": "services", "label": "Позиции аренды", "icon": ICON_SERVICES},
        {"url_name": "bookings", "label": "Брони", "icon": ICON_BOOKINGS},
        {"url_name": "analytics", "label": "Аналитика", "icon": ICON_ANALYTICS},
        {"url_name": "ai_assistant", "label": "AI-ассистент", "icon": ICON_AI},
        {"url_name": "settings", "label": "Настройки", "icon": ICON_SETTINGS},
    ],
}

DEFAULT_NAV = NAV_BY_TYPE["service"]

UI_TEXTS = {
    "service": {
        "service_title": "Услуги",
        "service_singular": "Услуга",
        "service_plural": "Услуги",
        "booking_title": "Записи",
        "booking_singular": "Запись",
        "booking_plural": "Записи",
    },
    "hotel": {
        "service_title": "Номера",
        "service_singular": "Номер",
        "service_plural": "Номера",
        "booking_title": "Бронирования",
        "booking_singular": "Бронирование",
        "booking_plural": "Бронирования",
    },
    "tour": {
        "service_title": "Туры",
        "service_singular": "Тур",
        "service_plural": "Туры",
        "booking_title": "Бронирования",
        "booking_singular": "Бронирование",
        "booking_plural": "Бронирования",
    },
    "event": {
        "service_title": "События",
        "service_singular": "Событие",
        "service_plural": "События",
        "booking_title": "Билеты",
        "booking_singular": "Билет",
        "booking_plural": "Билеты",
    },
    "rent": {
        "service_title": "Позиции аренды",
        "service_singular": "Позиция",
        "service_plural": "Позиции",
        "booking_title": "Брони",
        "booking_singular": "Бронь",
        "booking_plural": "Брони",
    },
}


def get_nav_items(unit):
    business_type = getattr(unit, "business_type", None) or "service"
    return NAV_BY_TYPE.get(business_type, DEFAULT_NAV)


def get_ui_texts(unit):
    business_type = getattr(unit, "business_type", None) or "service"
    base = UI_TEXTS["service"]
    return {**base, **UI_TEXTS.get(business_type, {})}


def get_dashboard_labels(ui_texts: dict):
    """
    Build a small set of labels for dashboard metrics & table headers.
    """
    return {
        "active_metric": f"Активные {ui_texts['booking_plural'].lower()}",
        "total_metric": f"Всего {ui_texts['booking_plural'].lower()}",
        "revenue_metric": "Выручка",
        "services_metric": ui_texts["service_plural"],
        "service_column": ui_texts["service_singular"],
    }


