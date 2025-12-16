import os
import requests
import time
import warnings
import uuid
import base64
from pathlib import Path
from dotenv import load_dotenv
from urllib3.exceptions import InsecureRequestWarning

# Грузим .env и из корня проекта, и из backend (рядом с manage.py)
PROJECT_ROOT = Path(__file__).resolve().parents[1]
BACKEND_ROOT = PROJECT_ROOT / "backend"
load_dotenv(PROJECT_ROOT / ".env", override=False)
load_dotenv(BACKEND_ROOT / ".env", override=False)

# Поддерживаем оба варианта названий переменных окружения для URL-ов (ключ передаётся вызовом)
AUTH_URL = "https://ngw.devices.sberbank.ru:9443/api/v2/oauth"
CHAT_URL = "https://gigachat.devices.sberbank.ru/api/v1/chat/completions"
DEFAULT_SCOPE = "GIGACHAT_API_PERS"
GIGACHAT_VERIFY_SSL = False

ACCESS_TOKEN = None
EXPIRES_AT = 0
CACHE_KEY = None  # cache key: (auth_key, scope)
warnings.filterwarnings("ignore", category=InsecureRequestWarning)


def _get_basic(auth_key: str | None):
    """
    Единственный источник: authorization_key (секрет) из БД, используем как есть (уже base64 id:secret).
    """
    auth_key = (auth_key or "").strip()
    if not auth_key:
        raise RuntimeError("GIGACHAT ERROR: missing GIGACHAT_AUTHORIZATION_KEY")
    lower = auth_key.lower()
    if lower.startswith("bearer ") or lower.startswith("basic "):
        raise RuntimeError("GIGACHAT ERROR: authorization key must be raw base64 (no 'Basic ' or 'Bearer ')")
    print("[GIGACHAT AUTH] key len:", len(auth_key), "prefix:", auth_key[:3], "suffix:", auth_key[-3:])
    return auth_key, auth_key


def get_gigachat_access_token(auth_key: str | None, scope: str | None = None, force_refresh=False):
    """
    Получение Access Token от GigaChat (OAuth).
    Возвращает token или бросает RuntimeError.
    """
    global ACCESS_TOKEN, EXPIRES_AT, CACHE_KEY

    basic, cache_key = _get_basic(auth_key)
    aurl = AUTH_URL
    scope_value = (scope or DEFAULT_SCOPE).strip() or DEFAULT_SCOPE

    print("[GIGACHAT TOKEN] requesting token, force_refresh:", force_refresh, "cached:", bool(ACCESS_TOKEN))

    now = time.time()
    if not force_refresh and ACCESS_TOKEN and CACHE_KEY == (cache_key, scope_value) and EXPIRES_AT - 30 > now:
        return ACCESS_TOKEN

    if force_refresh:
        print("[GIGACHAT TOKEN] refresh requested (force_refresh=True)")

    headers = {
        "Content-Type": "application/x-www-form-urlencoded",
        "Accept": "application/json",
        "RqUID": str(uuid.uuid4()),
        "Authorization": f"Basic {basic}",
    }
    print("[GIGACHAT TOKEN] auth header len:", len(basic), "prefix:", basic[:3], "suffix:", basic[-3:])

    data = f"scope={scope_value}"

    try:
        resp = requests.post(aurl, headers=headers, data=data, verify=GIGACHAT_VERIFY_SSL, timeout=30)
    except Exception as exc:
        print("[DIAG] GigaChat token exception:", type(exc).__name__, exc)
        raise RuntimeError(f"GIGACHAT EXCEPTION: {type(exc).__name__}: {exc}")

    print("[GIGACHAT TOKEN] url:", aurl)
    print("[GIGACHAT TOKEN] headers (sans auth):", {k: v for k, v in headers.items() if k.lower() != "authorization"})
    print("[GIGACHAT TOKEN] body:", data)
    print("[GIGACHAT TOKEN] status:", resp.status_code)
    print("[GIGACHAT TOKEN] resp body:", (resp.text or "")[:500])

    if resp.status_code != 200:
        raise RuntimeError(f"GIGACHAT ERROR: status={resp.status_code}, body={(resp.text or '')[:500]}")

    token = resp.json().get("access_token")
    expires_in = resp.json().get("expires_in", 600)
    ACCESS_TOKEN = token
    CACHE_KEY = (cache_key, scope_value)
    EXPIRES_AT = now + expires_in
    return token


def _chat_request(chat_url, headers, payload):
    try:
        resp = requests.post(
            chat_url or CHAT_URL,
            headers=headers,
            json=payload,
            timeout=30,
            verify=False,
        )
    except Exception as exc:
        print("[DIAG] GigaChat request exception:", type(exc).__name__, exc)
        raise RuntimeError(f"GIGACHAT EXCEPTION: {type(exc).__name__}: {exc}")

    print("[GIGACHAT CHAT] status:", resp.status_code)
    print("[GIGACHAT CHAT] body:", (resp.text or "")[:500])

    if resp.status_code == 200:
        try:
            content = resp.json()["choices"][0]["message"]["content"]
            return content, resp
        except Exception as exc:
            print("[DIAG] ask_gigachat parse error:", type(exc).__name__, exc)
            print("[DIAG] raw response snippet:", (resp.text or "")[:300])
            raise RuntimeError(f"GIGACHAT ERROR: status=200, body={(resp.text or '')[:500]}")

    raise RuntimeError(f"GIGACHAT ERROR: status={resp.status_code}, body={(resp.text or '')[:500]}")


def ask_gigachat(prompt: str, auth_key: str | None = None, client_id: str | None = None, chat_url: str | None = None, scope: str | None = None):
    """Отправка user-prompt в GigaChat"""

    auth_key = (auth_key or "").strip()
    if not auth_key:
        raise RuntimeError("GIGACHAT ERROR: authorization_key not provided")

    token = get_gigachat_access_token(auth_key=auth_key, scope=scope, force_refresh=False)

    headers = {
        "Authorization": f"Bearer {token}",
        "Content-Type": "application/json",
    }

    payload = {
        "model": "GigaChat:latest",
        "messages": [{"role": "user", "content": prompt}],
        "temperature": 0.3
    }

    try:
        content, resp = _chat_request(chat_url, headers, payload)
        return content
    except RuntimeError as exc:
        # если 401 — пробуем один refresh
        if "status=401" in str(exc):
            print("[GIGACHAT] received 401 from chat, refreshing token once")
            token = get_gigachat_access_token(auth_key=auth_key, scope=scope, force_refresh=True)
            headers["Authorization"] = f"Bearer {token}"
            content, resp = _chat_request(chat_url, headers, payload)
            return content
        raise
