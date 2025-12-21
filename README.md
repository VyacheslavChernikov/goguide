# SmartHotel / GoGuide Portal

Админ-портал и виджет бронирования для мульти-бизнеса (отели, услуги, туры, события).

## Основные возможности
- Отдельные админ-панели по типу бизнеса: услуги/номера, бронирования, аналитика, настройки.
- CRUD для услуг/номеров с модальными формами, дубликатами и 360°-превью.
- CRUD для бронирований/записей с валидацией пересечений, CSV-экспортом и статусами оплаты.
- Бронирования через публичный Web Component (`booking-widget.js`), поддержка 360° виджетов и кастомизации (цвета, тексты, ширина, автопрокрутка, авто-открытие превью).
- AI-ассистент с контекстом из площадки, услуг и бронирований.
- Темы портала: dark/light.
- Настройка виджета в админке (пресеты, превью, генерация embed-кода).
- Оплаты: поля оплаты в бронированиях (статус/провайдер/id/сумма/мета), сохранение статуса в админке и отображение в виджете.
- Выплаты: реквизиты для выводов, учёт баланса по оплаченных бронированиям, заявки на вывод, таблица выплат, мастер подключения провайдера (manual/mock/YooKassa/CloudPayments/Тинькофф) с webhook URL и тестовой выплатой.

## Быстрый старт (dev)
```bash
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
python manage.py migrate
python manage.py runserver
```

## Деплой в Docker (backend)
```bash
# сборка образа (multi-stage, gunicorn):
docker build -t smarthotel-backend -f backend/Dockerfile backend

# переменные окружения (пример)
cat > .env <<'EOF'
SECRET_KEY=change-me
DEBUG=0
ALLOWED_HOSTS=your-domain.com
DB_HOST=postgres
DB_PORT=5432
DB_NAME=smarthotel
DB_USER=smarthotel
DB_PASSWORD=smarthotel
# GigaChat (опционально, можно вводить через портал)
GIGACHAT_BASIC_AUTH=base64_or_token
GIGACHAT_CLIENT_ID=your_client_id
GIGACHAT_SCOPE=GIGACHAT_API_PERS
EOF

# запустить, пробросив порт
docker run -d --name smarthotel-backend \
  --env-file .env \
  -p 8000:8000 \
  smarthotel-backend
```
- На старте entrypoint выполнит `python manage.py migrate`, затем запустит gunicorn (`PORT/WORKERS/THREADS/TIMEOUT` можно задать env).
- Для прод окружения добавьте прокси/HTTPS и корректный `ALLOWED_HOSTS`.
- Статика собирается на этапе сборки (`collectstatic`), DB должна быть доступна (Postgres).

## Ключевые файлы
- `backend/go_guide_portal/views.py` — логика портала, CRUD, выплаты, вебхук.
- `backend/go_guide_portal/templates/go_guide_portal/` — страницы портала (услуги, бронирования, аналитика, настройки).
- `backend/go_guide_portal/static/widget/booking-widget.js` — веб-компонент бронирования.
- `backend/business_units/models.py` — модель площадки, реквизиты и конфиг выплат, модель выплат.
- `backend/appointments/models.py` — бронирования с платежными полями.
- `backend/api/` — открытые API для услуг и создания бронирований.

## Выплаты (payouts)
- Провайдер и режим задаются в настройках площадки (manual/mock/YooKassa/CloudPayments/Тинькофф).
- Вкладка «Выплаты»: подключение провайдера (ключ/secret/webhook secret), URL вебхука, тестовая выплата 1 ₽, баланс, выводы и список выплат.
- Вебхук: `dashboard/payouts/webhook/` принимает `payout_id/id/provider_payout_id` и `status`. Для боевых провайдеров нужно добавить проверку подписи и реальные вызовы API (сейчас заглушка/mock/processing).

## Темизация и виджет
- Темы портала: переключатель dark/light хранится в `BusinessUnit.portal_theme`.
- Виджет читает конфиг из data-атрибутов/`widget_config`; поддерживает 360° в iframe через `tour_widget` услуги.

## Что доработать для боевых выплат
- Реальные вызовы API (YooKassa/CloudPayments/Тинькофф) в `_initiate_payout`.
- Проверка подписи вебхука по секрету провайдера.
- Приём KYC/реквизитов в нужном формате и валидация перед вызовом payout API.

---

Лицензия: MIT.
