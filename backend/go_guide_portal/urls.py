from django.urls import path
from . import views

urlpatterns = [
    path("login/", views.login_view, name="go_guide_login"),
    path("dashboard/", views.dashboard, name="go_guide_dashboard"),
    path("dashboard/rooms/", views.rooms_view, name="rooms"),
    path("dashboard/bookings/", views.bookings_view, name="bookings"),
    path("dashboard/rooms/create/", views.room_create, name="room_create"),
    path("dashboard/rooms/<int:pk>/update/", views.room_update, name="room_update"),
    path("dashboard/rooms/<int:pk>/delete/", views.room_delete, name="room_delete"),
    path("dashboard/bookings/create/", views.booking_create, name="booking_create"),
    path("dashboard/bookings/<int:pk>/update/", views.booking_update, name="booking_update"),
    path("dashboard/bookings/<int:pk>/delete/", views.booking_delete, name="booking_delete"),
    path("dashboard/bookings/export/", views.bookings_export_csv, name="bookings_export"),
    path("dashboard/services/", views.services_view, name="services"),
    path("dashboard/appointments/", views.appointments_view, name="appointments"),
    path("dashboard/analytics/", views.analytics_view, name="analytics"),
    path("dashboard/ai-assistant/", views.ai_assistant_view, name="ai_assistant"),
    path("dashboard/chat-with-ai/", views.chat_with_ai, name="chat_with_ai"),
    path("dashboard/integrations/gigachat/", views.gigachat_settings_view, name="gigachat_settings"),
    path("dashboard/knowledge/", views.knowledge_upload, name="knowledge_upload"),
    path("dashboard/settings/", views.settings_view, name="settings"),
    path("dashboard/tours/", views.tours_view, name="tours"),
]

