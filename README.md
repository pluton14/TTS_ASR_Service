# TTS + ASR Pipeline

Микросервисная система для синтеза и распознавания речи.

## Архитектура

- **tts-service** - синтез речи (gTTS)
- **asr-service** - распознавание речи (Whisper)  
- **gateway** - маршрутизация запросов
- **client** - тестовые скрипты

## Запуск

1. Клонировать репозиторий
2. Скопировать `.env.example` в `.env`
3. Запустить сервисы:

```bash
docker-compose up --build
```

4. Дождаться загрузки моделей (1-2 минуты)

## Тестирование

### TTS через WebSocket
```bash
python client/stream_tts.py
```

### ASR + TTS pipeline
```bash
python client/echo_bytes.py
```

## API

**Gateway (порт 8000):**
- `GET /health` - проверка здоровья
- `POST /api/echo-bytes` - ASR + TTS pipeline
- `WS /ws/tts` - WebSocket для TTS

**TTS Service (порт 8082):**
- `POST /api/tts` - HTTP синтез речи
- `WS /ws/tts` - WebSocket синтез

**ASR Service (порт 8081):**
- `POST /api/stt/bytes` - распознавание речи

## Требования

- Docker
- Python 3.11+
- Интернет для gTTS

## Переменные окружения

Основные настройки в `.env`:
- `TTS_LANGUAGE=en` - язык для TTS
- `ASR_MODEL_NAME=base.en` - модель Whisper
- `LOG_LEVEL=INFO` - уровень логирования
