FROM python:3.11-alpine

# Установка зависимостей для Alpine
RUN apk update && apk add --no-cache \
    gcc \
    musl-dev \
    postgresql-dev

# Рабочая директория
WORKDIR /app

# Копируем зависимости
COPY requirements.txt .

# Устанавливаем зависимости
RUN pip install --no-cache-dir -r requirements.txt

# Копируем проект
COPY src/ .

# Открываем порт
EXPOSE 8000

# Команда запуска
CMD ["python", "manage.py", "runserver", "0.0.0.0:8000"]
