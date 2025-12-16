from fastapi import FastAPI

app = FastAPI(title="SmartHotel API")


@app.get("/ping")
def ping():
    return {"status": "ok"}


@app.post("/api/{hotel_slug}/check")
def check_availability(hotel_slug: str):
    """
    Черновой эндпоинт проверки доступности отеля.
    Пока просто возвращает hotel_slug, дальше привяжем к базе.
    """
    return {
        "hotel": hotel_slug,
        "status": "ok",
        "message": "Проверка доступности работает (заглушка)."
    }


@app.post("/api/{hotel_slug}/reserve")
def reserve_room(hotel_slug: str):
    """
    Черновой эндпоинт бронирования.
    Сейчас заглушка, позже сюда прикрутим логику и AI.
    """
    return {
        "hotel": hotel_slug,
        "result": "reserved_mock",
        "message": "Бронирование пока фейковое, но API жив."
    }
