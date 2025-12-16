import os
import logging
from typing import Optional
from datetime import datetime

from aiogram import Bot, Dispatcher, F
from aiogram.filters import CommandStart, Command
from aiogram.types import (
    Message, CallbackQuery,
    InlineKeyboardMarkup, InlineKeyboardButton,
    ReplyKeyboardMarkup, KeyboardButton
)
from aiogram.client.default import DefaultBotProperties
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import StatesGroup, State
from aiogram.fsm.storage.memory import MemoryStorage

import httpx
from dotenv import load_dotenv

# RAG + GigaChat
from rag import SmartHotelRAG
from gigachat_ai import ask_gigachat


# ===================================================
# НАСТРОЙКИ
# ===================================================
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
load_dotenv()

BOT_TOKEN = os.getenv("BOT_TOKEN")

# ВАЖНО: base_url ВСЕГДА заканчивается на /api/
API_BASE_URL = os.getenv("API_BASE_URL", "http://smarthotel_backend:8000/api/")

bot = Bot(token=BOT_TOKEN, default=DefaultBotProperties(parse_mode="HTML"))
dp = Dispatcher(storage=MemoryStorage())
rag = SmartHotelRAG()


# Проверка: работает ли бот?
@dp.message(Command("start"))
async def start_command(message: Message):
    await message.answer(
        "🌟 Добро пожаловать в SmartHotel!\n\n"
        "Я ваш личный виртуальный консьерж. Готов помочь с:\n"
        "🔹 Выбором отеля\n"
        "🔹 Информацией о номерах и услугах\n"
        "🔹 Бронированием\n"
        "🔹 360° турами по номерам\n\n"
        "Нажмите кнопку «Отели» или спросите меня прямо здесь — я всегда на связи!",
        reply_markup=bottom_menu(),
    )


# ===================================================
# УТИЛИТЫ ДЛЯ API
# ===================================================

def clean_path(path: str) -> str:
    """Убираем ведущий слеш — httpx иначе перезатирает путь."""
    return path.lstrip("/")


async def api_get(path: str, params=None):
    path = clean_path(path)

    try:
        async with httpx.AsyncClient(base_url=API_BASE_URL, timeout=10.0) as client:
            r = await client.get(path, params=params)
            r.raise_for_status()
            return r.json()

    except httpx.HTTPStatusError as e:
        logging.error(f"API GET status error {path}: {e}")
        return []
    except Exception as e:
        logging.error(f"API GET error {path}: {e}")
        return []


async def api_post(path: str, data: dict):
    path = clean_path(path)

    try:
        async with httpx.AsyncClient(base_url=API_BASE_URL, timeout=10.0) as client:
            r = await client.post(path, json=data)
            r.raise_for_status()
            return r.json()

    except Exception as e:
        logging.error(f"API POST error {path}: {e}")
        raise


# ===================================================
# КОНСТАНТЫ
# ===================================================

ROOM_TOURS = {
    "семейный": "https://goguide.ru/tour/1255",
    "стандарт 1": "https://goguide.ru/tour/1248",
    "стандарт 2": "https://goguide.ru/tour/1260",
    "стандарт 3": "https://goguide.ru/tour/1262",
    "стандарт 4": "https://goguide.ru/tour/1254",
    "стандарт 5": "https://goguide.ru/tour/1250",
    "стандарт 6": "https://goguide.ru/tour/1261",
}


def extract_room_query(text: str) -> Optional[str]:
    text = text.lower().strip()

    if "семейн" in text:
        return "семейный"

    for i in range(1, 7):
        if f"номер {i}" in text or text == str(i):
            return f"стандарт {i}"

    if "стандарт" in text:
        return "стандарт 1"

    return None


# ===================================================
# FSM STATES
# ===================================================
class AiStates(StatesGroup):
    ai_mode = State()


class BookingStates(StatesGroup):
    choosing_hotel = State()
    choosing_room = State()
    entering_date_from = State()
    entering_date_to = State()
    entering_guest_name = State()
    entering_phone = State()
    entering_email = State()
    confirming = State()


BOOKING_TRIGGER_PHRASES = [
    "забронируй",
    "забронировать",
    "хочу забронировать",
    "давай бронь",
    "давай забронируем",
    "беру",
    "забираю",
    "оформи",
    "хочу снять",
    "забронировать номер",
]


def bottom_menu():
    return ReplyKeyboardMarkup(
        keyboard=[
            [KeyboardButton(text="🏢 Отели"), KeyboardButton(text="🎥 Туры 360°")]
        ],
        resize_keyboard=True,
    )


def hotel_keyboard(hotels: list) -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [InlineKeyboardButton(text=h["name"], callback_data=f"select_hotel:{h['id']}")]
            for h in hotels
        ]
    )


# ===================================================
# START
# ===================================================
@dp.message(CommandStart())
async def cmd_start(message: Message, state: FSMContext):
    await state.clear()
    await state.set_state(AiStates.ai_mode)
    await message.answer(
        "🌟 Добро пожаловать в SmartHotel!\n\n"
        "Я ваш личный виртуальный консьерж. Готов помочь с:\n\n"
        "🔹 Выбором отеля\n"
        "🔹 Информацией о номерах и услугах\n"
        "🔹 Бронированием\n"
        "🔹 360° турами по номерам\n\n"
        "Нажмите кнопку «Отели» или спросите меня прямо здесь — я всегда на связи!",
        reply_markup=bottom_menu(),
    )


# ===================================================
# СПИСОК ОТЕЛЕЙ
# ===================================================
@dp.message(F.text == "🏢 Отели")
async def list_hotels(message: Message, state: FSMContext):
    hotels = await api_get("hotels/")

    if not hotels:
        await message.answer("Отелей пока нет.", reply_markup=bottom_menu())
        return

    for h in hotels:
        caption = (
            f"🏨 <b>{h['name']}</b>\n"
            f"📍 {h['address']}\n"
            f"{h.get('description', '')[:120]}...\n\n"
            "Нажмите кнопку ниже, чтобы выбрать этот отель."
        )

        kb = InlineKeyboardMarkup(
            inline_keyboard=[
                [InlineKeyboardButton(text="Выбрать отель", callback_data=f"select_hotel:{h['id']}")]
            ]
        )

        photo_url = h.get("photo_url")
        if photo_url and photo_url.strip():
            try:
                await bot.send_photo(
                    chat_id=message.chat.id,
                    photo=photo_url.strip(),
                    caption=caption,
                    reply_markup=kb
                )
            except Exception:
                await message.answer(text=caption, reply_markup=kb)
        else:
            await message.answer(text=caption, reply_markup=kb)

    await message.answer("👇 Выберите отель, чтобы продолжить.", reply_markup=bottom_menu())


@dp.callback_query(F.data.startswith("select_hotel:"))
async def select_hotel(callback: CallbackQuery, state: FSMContext):
    hotel_id = int(callback.data.split(":")[1])
    hotels = await api_get("hotels/")
    hotel = next((h for h in hotels if h["id"] == hotel_id), None)

    if not hotel:
        await callback.answer("Отель не найден", show_alert=True)
        return

    await state.update_data(
        selected_hotel_id=hotel_id,
        selected_hotel_name=hotel["name"],
    )

    await callback.message.edit_text(
        f"✅ Вы выбрали отель <b>{hotel['name']}</b>."
    )
    await callback.message.answer(
        "Теперь можете спрашивать про номера, услуги или начать бронирование.",
        reply_markup=bottom_menu(),
    )
    await callback.answer()


# ===================================================
# ТУРЫ 360°
# ===================================================
@dp.message(F.text == "🎥 Туры 360°")
async def reply_tours(message: Message, state: FSMContext):
    hotels = await api_get("hotels/")

    if not hotels:
        await message.answer("Пока нет отелей с турами 360°.", reply_markup=bottom_menu())
        return

    kb = InlineKeyboardMarkup(
        inline_keyboard=[[InlineKeyboardButton(h["name"], callback_data=f"tourhotel:{h['id']}")] for h in hotels]
    )

    await message.answer("Выберите отель:", reply_markup=kb)


# ===================================================
# AI ЧАТ
# ===================================================
@dp.message(AiStates.ai_mode)
async def handle_message(message: Message, state: FSMContext):
    text = (message.text or "").strip()
    if not text:
        return

    data = await state.get_data()
    selected_hotel_name = data.get("selected_hotel_name")

    hotels = await api_get("hotels/")
    for h in hotels:
        if h["name"].lower() in text.lower():
            await state.update_data(
                selected_hotel_id=h["id"],
                selected_hotel_name=h["name"],
            )
            await message.answer(
                f"Вы выбрали отель <b>{h['name']}</b>.\n"
                "Теперь можете спрашивать про номера или начать бронирование.",
                reply_markup=bottom_menu(),
            )
            return

    # запрос про конкретный номер
    room_key = extract_room_query(text)
    if room_key:
        hotel_id = data.get("selected_hotel_id")
        if not hotel_id:
            await message.answer("Сначала выберите отель через «Отели».", reply_markup=bottom_menu())
            return

        rooms = await api_get("rooms/", params={"hotel": hotel_id})
        found = None

        for r in rooms:
            if room_key == "семейный" and "семейн" in r["room_type"].lower():
                found = r
                break
            if room_key.endswith(str(r["room_number"])):
                found = r
                break

        if found:
            tour = ROOM_TOURS.get(room_key)
            kb = InlineKeyboardMarkup(
                inline_keyboard=[[InlineKeyboardButton("Открыть 360° тур", url=tour)]] if tour else []
            )

            await message.answer(
                f"<b>{found['room_type']}</b>\n"
                f"Номер: {found['room_number']}\n"
                f"Цена: {found['price_per_night']} ₽/ночь\n\n"
                "Чтобы забронировать — напишите «забронировать».",
                reply_markup=kb or bottom_menu(),
            )
            return

    # запуск бронирования
    if any(p in text.lower() for p in BOOKING_TRIGGER_PHRASES):
        await start_booking(message, state)
        return

    # RAG
    context = rag.query(text, hotel=selected_hotel_name) if selected_hotel_name else ""

    if selected_hotel_name:
        prompt = (
            f"Ты — консьерж отеля «{selected_hotel_name}». "
            "Отвечай только по фактам из контекста или ответь: "
            "«Уточните у администратора отеля»."
        )
    else:
        prompt = "Ты — консьерж SmartHotel. Посоветуй выбрать отель через кнопку «Отели»."

    answer = ask_gigachat(f"{prompt}\n\nКонтекст:\n{context}\n\nВопрос:\n{text}")
    await message.answer(answer, reply_markup=bottom_menu())


# ===================================================
# БРОНИРОВАНИЕ (осталось без изменений)
# ===================================================
async def start_booking(message_or_callback, state: FSMContext):
    hotels = await api_get("hotels/")

    if not hotels:
        msg = message_or_callback if isinstance(message_or_callback, Message) else message_or_callback.message
        await msg.answer("Отелей пока нет.", reply_markup=bottom_menu())
        return

    kb = InlineKeyboardMarkup(
        inline_keyboard=[[InlineKeyboardButton(h["name"], callback_data=f"hotel:{h['id']}")] for h in hotels]
    )

    msg = message_or_callback if isinstance(message_or_callback, Message) else message_or_callback.message
    await msg.answer("Выберите отель:", reply_markup=kb)
    await state.set_state(BookingStates.choosing_hotel)


@dp.callback_query(F.data.startswith("hotel:"), BookingStates.choosing_hotel)
async def choose_hotel(callback: CallbackQuery, state: FSMContext):
    hotel_id = int(callback.data.split(":")[1])

    hotels = await api_get("hotels/")
    hotel = next((h for h in hotels if h["id"] == hotel_id), None)

    if not hotel:
        await callback.answer("Отель не найден", show_alert=True)
        return

    await state.update_data(
        selected_hotel_id=hotel_id,
        selected_hotel_name=hotel["name"],
    )

    rooms = await api_get("rooms/", params={"hotel": hotel_id})
    available = [r for r in rooms if r.get("is_available", True)]

    if not available:
        await callback.message.edit_text(
            f"В {hotel['name']} нет свободных номеров.",
            reply_markup=bottom_menu(),
        )
        await state.set_state(AiStates.ai_mode)
        return

    kb = InlineKeyboardMarkup(
        inline_keyboard=[
            [InlineKeyboardButton(f"{r['room_type']} №{r['room_number']}", callback_data=f"room:{r['id']}")]
            for r in available
        ]
    )

    text = (
        f"Свободные номера в {hotel['name']}:\n\n" +
        "\n".join(f"• {r['room_number']} — {r['room_type']} — {r['price_per_night']} ₽" for r in available)
        + "\n\nВыберите номер:"
    )

    await callback.message.edit_text(text, reply_markup=kb)
    await state.set_state(BookingStates.choosing_room)


@dp.callback_query(F.data.startswith("room:"), BookingStates.choosing_room)
async def choose_room(callback: CallbackQuery, state: FSMContext):
    room_id = int(callback.data.split(":")[1])
    room = await api_get(f"rooms/{room_id}/")

    await state.update_data(
        selected_room_id=room_id,
        selected_room_type=room["room_type"],
        selected_room_price=room["price_per_night"],
    )

    await callback.message.edit_text("📅 Введите дату заезда (ДД.ММ.ГГГГ):")
    await state.set_state(BookingStates.entering_date_from)


# ===================================================
# Финальные шаги бронирования (оставил без изменений)
# ===================================================
@dp.message(BookingStates.entering_date_from)
async def booking_date_from(message: Message, state: FSMContext):
    await state.update_data(date_from=message.text.strip())
    await message.answer("📅 Теперь дату выезда (ДД.ММ.ГГГГ):")
    await state.set_state(BookingStates.entering_date_to)


@dp.message(BookingStates.entering_date_to)
async def booking_date_to(message: Message, state: FSMContext):
    await state.update_data(date_to=message.text.strip())
    await message.answer("Как вас зовут?")
    await state.set_state(BookingStates.entering_guest_name)


@dp.message(BookingStates.entering_guest_name)
async def booking_guest(message: Message, state: FSMContext):
    await state.update_data(guest_name=message.text.strip())
    await message.answer("Ваш телефон:")
    await state.set_state(BookingStates.entering_phone)


@dp.message(BookingStates.entering_phone)
async def booking_phone(message: Message, state: FSMContext):
    await state.update_data(guest_phone=message.text.strip())
    await message.answer("Email (или напишите «-»):")
    await state.set_state(BookingStates.entering_email)


@dp.message(BookingStates.entering_email)
async def booking_email(message: Message, state: FSMContext):
    email = message.text.strip()
    if email == "-":
        email = ""

    await state.update_data(guest_email=email)
    data = await state.get_data()

    try:
        d1 = datetime.strptime(data["date_from"], "%d.%m.%Y").date()
        d2 = datetime.strptime(data["date_to"], "%d.%m.%Y").date()
        nights = max((d2 - d1).days, 1)
    except:
        nights = 1

    price_per_night = float(data.get("selected_room_price", 0))
    total = price_per_night * nights

    payload = {
        "hotel": data["selected_hotel_id"],
        "room": data["selected_room_id"],
        "guest_name": data["guest_name"],
        "guest_phone": data["guest_phone"],
        "guest_email": data["guest_email"],
        "date_from": data["date_from"],
        "date_to": data["date_to"],
        "total_price": str(total),
        "is_confirmed": False,
    }

    try:
        booking = await api_post("booking/", payload)
        booking_id = booking.get("id", "—")

        await message.answer(
            f"Бронь создана!\n\n"
            f"Номер брони: {booking_id}\n"
            f"Отель: {data['selected_hotel_name']}\n"
            f"Номер: {data['selected_room_type']}\n"
            f"Заезд: {data['date_from']}\n"
            f"Выезд: {data['date_to']}\n"
            f"Гость: {data['guest_name']}\n"
            f"Телефон: {data['guest_phone']}",
            reply_markup=bottom_menu(),
        )

    except Exception as e:
        logging.error(f"Booking create error: {e}")
        await message.answer(
            "Не удалось создать бронь. Попробуйте снова.",
            reply_markup=bottom_menu(),
        )

    await state.set_state(AiStates.ai_mode)


# ===================================================
# ТУРЫ 360°
# ===================================================
@dp.callback_query(F.data.startswith("tourhotel:"))
async def choose_tour_hotel(callback: CallbackQuery):
    hotel_id = int(callback.data.split(":")[1])
    rooms = await api_get("rooms/", params={"hotel": hotel_id})

    if not rooms:
        await callback.message.answer("Нет номеров с 360° туром.", reply_markup=bottom_menu())
        return

    kb = InlineKeyboardMarkup(
        inline_keyboard=[
            [InlineKeyboardButton(f"{r['room_type']} №{r['room_number']}", callback_data=f"tourroom:{r['room_number']}")]
            for r in rooms
        ]
    )
    await callback.message.edit_text("Выберите номер:", reply_markup=kb)


@dp.callback_query(F.data.startswith("tourroom:"))
async def open_tour(callback: CallbackQuery):
    num = callback.data.split(":")[1]
    key = "семейный" if num == "семейный" else f"стандарт {num}"

    link = ROOM_TOURS.get(key)
    if not link:
        await callback.message.answer("Тур не найден.", reply_markup=bottom_menu())
        return

    kb = InlineKeyboardMarkup(inline_keyboard=[[InlineKeyboardButton("Открыть 360° тур", url=link)]])
    await callback.message.answer(f"Тур по номеру {num}:", reply_markup=kb)


# ===================================================
# ЗАПУСК
# ===================================================
async def main():
    await dp.start_polling(bot)


if __name__ == "__main__":
    import asyncio
    asyncio.run(main())
