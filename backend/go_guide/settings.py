import os
import sys
from pathlib import Path
from dotenv import load_dotenv

# ====================================
# LOAD ENV
# ====================================
BASE_DIR = Path(__file__).resolve().parent.parent
PROJECT_ROOT = BASE_DIR.parent

# грузим .env из корня и из backend, чтобы web-процесс видел ключи Gigachat
load_dotenv(PROJECT_ROOT / ".env", override=False)
load_dotenv(BASE_DIR / ".env", override=False)

# GigaChat credentials (проверка выполняется в момент обращения к API, не при старте Django)
GIGACHAT_CLIENT_ID = os.getenv("GIGACHAT_CLIENT_ID")
GIGACHAT_AUTHORIZATION_KEY = os.getenv("GIGACHAT_AUTHORIZATION_KEY")

# Добавляем корень проекта (над backend) в sys.path, чтобы импортировать пакеты вроде "bot"
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

# ====================================
# SECURITY
# ====================================
SECRET_KEY = os.getenv("SECRET_KEY", "django-insecure-please-change-in-prod")
DEBUG = os.getenv("DEBUG", "True") == "True"  # ← В dev пусть будет True

# ← ИСПРАВЛЕНО: ALLOWED_HOSTS — разрешаем доступ из бота по имени сервиса
ALLOWED_HOSTS = [
    'localhost',
    '127.0.0.1',
    'backend',               # ← имя сервиса в Docker Compose
    'smarthotel_backend',    # ← container_name (на всякий случай)
]
DEBUG = True

# ====================================
# APPS
# ====================================
INSTALLED_APPS = [
    'django.contrib.admin',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.messages',
    'django.contrib.staticfiles',

    # Project apps
    'api',
    'appointments.apps.AppointmentsConfig',
    'business_units.apps.BusinessUnitsConfig',
    'services.apps.ServicesConfig',

    # Third-party
    'rest_framework',
    'corsheaders',

    # Custom
    'go_guide_portal.apps.GoGuidePortalConfig',
]

# ====================================
# MIDDLEWARE
# ====================================
MIDDLEWARE = [
    'corsheaders.middleware.CorsMiddleware',  # ← ДОЛЖЕН быть САМЫМ ПЕРВЫМ!
    'django.middleware.security.SecurityMiddleware',
    'django.contrib.sessions.middleware.SessionMiddleware',
    'django.middleware.common.CommonMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
    'django.middleware.clickjacking.XFrameOptionsMiddleware',
]

# ====================================
# URL / WSGI / ASGI
# ====================================
ROOT_URLCONF = 'go_guide.urls'
WSGI_APPLICATION = 'go_guide.wsgi.application'
ASGI_APPLICATION = 'go_guide.asgi.application'

# ====================================
# TEMPLATES
# ====================================
TEMPLATES = [
    {
        'BACKEND': 'django.template.backends.django.DjangoTemplates',
        'DIRS': [BASE_DIR / "admin_custom" / "templates", BASE_DIR / "go_guide_portal" / "templates", BASE_DIR / "templates"],
        'APP_DIRS': True,
        'OPTIONS': {
            'context_processors': [
                'django.template.context_processors.debug',
                'django.template.context_processors.request',
                'django.contrib.auth.context_processors.auth',
                'django.contrib.messages.context_processors.messages',
                'go_guide_portal.context_processors.portal_context',
            ],
        },
    },
]

# ====================================
# DATABASE: SQLITE FOR LOCAL DEV, POSTGRES FOR DOCKER/PROD
# ====================================
USE_SQLITE = os.getenv("DB_SQLITE", "True") == "True"

if USE_SQLITE:
    DATABASES = {
        "default": {
            "ENGINE": "django.db.backends.sqlite3",
            "NAME": BASE_DIR / "db.sqlite3",
        }
    }
else:
    DATABASES = {
        "default": {
            "ENGINE": "django.db.backends.postgresql",
            "NAME": os.getenv("POSTGRES_DB", os.getenv("DB_NAME", "smarthotel")),
            "USER": os.getenv("POSTGRES_USER", os.getenv("DB_USER", "smarthotel")),
            "PASSWORD": os.getenv("POSTGRES_PASSWORD", os.getenv("DB_PASSWORD", "smarthotel")),
            "HOST": os.getenv("POSTGRES_HOST", os.getenv("DB_HOST", "postgres")),
            "PORT": os.getenv("POSTGRES_PORT", os.getenv("DB_PORT", "5432")),
        }
    }

# ====================================
# PASSWORD VALIDATION
# ====================================
AUTH_PASSWORD_VALIDATORS = [
    {'NAME': 'django.contrib.auth.password_validation.UserAttributeSimilarityValidator'},
    {'NAME': 'django.contrib.auth.password_validation.MinimumLengthValidator'},
    {'NAME': 'django.contrib.auth.password_validation.CommonPasswordValidator'},
    {'NAME': 'django.contrib.auth.password_validation.NumericPasswordValidator'},
]

# ====================================
# I18N
# ====================================
LANGUAGE_CODE = 'ru-ru'
TIME_ZONE = 'Europe/Moscow'
USE_I18N = True
USE_TZ = True

# ====================================
# STATIC & MEDIA
# ====================================
STATIC_URL = '/static/'
STATIC_ROOT = BASE_DIR / "staticfiles"

MEDIA_URL = '/media/'
MEDIA_ROOT = BASE_DIR / "media"

# ====================================
# CORS
# ====================================
CORS_ALLOW_ALL_ORIGINS = True  # ← OK для dev

# ====================================
# DRF
# ====================================
REST_FRAMEWORK = {
    'DEFAULT_PERMISSION_CLASSES': [
        'rest_framework.permissions.AllowAny',
    ]
}

DEFAULT_AUTO_FIELD = 'django.db.models.BigAutoField'

STATICFILES_DIRS = [
    BASE_DIR / "admin_custom" / "static",
    BASE_DIR / "go_guide_portal" / "static",
]

LOGOUT_REDIRECT_URL = "/login/"
LOGIN_URL = "/login/"
LOGIN_REDIRECT_URL = "/dashboard/"