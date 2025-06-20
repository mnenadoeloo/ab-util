FROM harbor.wildberries.ru/docker-hub-proxy/python:3.10-slim

WORKDIR /app

# Установка Poetry
RUN pip install poetry==1.7.1

# Копирование файлов зависимостей
COPY pyproject.toml poetry.lock ./

# Настройка Poetry для установки зависимостей в системный путь Python
# вместо создания виртуального окружения
RUN poetry config virtualenvs.create false

# Установка зависимостей
RUN poetry install --no-dev --no-interaction --no-ansi

# Копирование кода приложения
COPY app/ ./app/
COPY config.yaml ./

ENV PROMETHEUS_MODULE=app.prometheus_metrics

# Порт, который будет использовать приложение
EXPOSE 8000

# Запуск приложения
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"] 