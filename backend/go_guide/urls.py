"""
URL configuration for config project.

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/5.2/topics/http/urls/
Examples:
Function views
    1. Add an import:  from my_app import views
    2. Add a URL to urlpatterns:  path('', views.home, name='home')
Class-based views
    1. Add an import:  from other_app.views import Home
    2. Add a URL to urlpatterns:  path('', Home.as_view(), name='home')
Including another URLconf
    1. Import the include() function: from django.urls import include, path
    2. Add a URL to urlpatterns:  path('blog/', include('blog.urls'))
"""
from django.contrib import admin
from django.contrib.auth.views import LogoutView
from django.urls import path, include
from django.shortcuts import render, redirect
from django.views.generic import RedirectView


# Главная страница (лендинг Go&Guide)
def home(request):
    return redirect("go_guide_login")


urlpatterns = [
    # Админка
    path("admin/", admin.site.urls),

    # API
    path("api/", include("api.urls")),

    # Кабинет Go&Guide
    path("", include("go_guide_portal.urls")),

    # Совместимость: редирект стандартного accounts/login на наш /login/
    path("accounts/login/", RedirectView.as_view(url="/login/", permanent=False)),

    # Главная страница
    path("", home, name="home"),

    # Logout → /login/
    path("logout/", LogoutView.as_view(next_page="/login/"), name="logout"),
]


