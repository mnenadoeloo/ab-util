# A/B Testing Router / Балансировщик

Сервис для балансировки запросов между различными сервисами для A/B-тестирования.

## Особенности

- Балансировка запросов между двумя сервисами с учетом весов
- Поддержка режимов работы с одним или двумя сервисами
- Механизм резервирования при недоступности сервиса
- Конфигурация через YAML-файл
- Гибкая настройка параметров

## Требования

- Python 3.8+
- Poetry (для управления зависимостями)

## Установка

1. Клонировать репозиторий
2. Установить зависимости с помощью Poetry:

```bash
# Установка Poetry (если не установлен)
curl -sSL https://install.python-poetry.org | python3 -

# Установка зависимостей
poetry install
```

## Конфигурация

Настройки хранятся в файле `config.yaml` в корне проекта:

```yaml
# Режим работы: "single" - один сервис, "dual" - два сервиса, "triple" - три сервиса
mode: triple

# Конфигурация сервисов
services:
  service_v1:
    url: http://localhost:8000/api/v1/llm/generate-responses_api
    weight: 0.33
  service_v2:
    url: http://localhost:8001/api/v1/llm/generate-responses
    weight: 0.33
  service_v2:
    url: http://localhost:8001/api/v1/llm/generate-responses
    weight: 0.33

# Таймаут для запросов к сервисам (в секундах)
timeout: 35

# Если True, в случае недоступности одного сервиса перенаправляет на другой
fallback_enabled: true
```

## Запуск

```bash
# Запуск через Poetry
poetry run uvicorn app.main:app --reload

# Или через активацию виртуального окружения
poetry shell
uvicorn app.main:app --reload
```

## API

### POST /respond

Обрабатывает запрос и перенаправляет его на один из сервисов.

**Запрос:**
```json
{
    "id": 0001,
    "wbUserId": 1001,
    "userName": "Иван",
    "nmId": 1010101100101,
    "review": "Крутой чехол!",
    "rating": 5
}
```

**Ответ:**
```json
{
  "response": "...",
  "metadata": {
    "id_review": 0001,
    "id_user": 1001,
    "user_name": "Иван",
    "nm_id": 1010101100101,
    "review": "Крутой чехол! Плюсы: ... Минусы: ...",
    "rating": 5
  },
  "product_data": {
    "title": "...",
    "category": "..."
  }
}
```

### GET /health

Эндпоинт для проверки работоспособности сервиса.

**Ответ:**
```json
{
  "status": "ok"
}
```

### GET /config

Информация о текущей конфигурации балансировщика.

**Ответ:**
```json
{
  "mode": "triple",
  "services": {
    "service_v1": {"url": "http://localhost:8000/respond", "weight": 0.33},
    "service_v2": {"url": "http://localhost:8001/respond", "weight": 0.33},
    "service_v3": {"url": "http://localhost:8001/respond", "weight": 0.33}
  },
  "timeout": 5,
  "fallback_enabled": true
}
```

