FROM python:3.12-slim

# Устанавливаем дополнительные пакеты (если понадобятся)
RUN apt-get update && apt-get install -y \
    build-essential \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app

COPY requirements.txt /app/
RUN pip install --no-cache-dir -r requirements.txt

COPY . /app/

# Файл .env будет подключаться через docker-compose
ENV PYTHONUNBUFFERED=1

CMD ["python", "bot.py"]

