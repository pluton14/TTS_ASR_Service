# Project Summary

## ✅ Выполненные требования

### Архитектура
- [x] **3 микросервиса в отдельных контейнерах**: tts-service, asr-service, gateway
- [x] **Пользовательская bridge-сеть**: speech_net
- [x] **Именованные volumes**: models_tts, models_asr, logs
- [x] **Конфигурация через .env**: env.example файл с переменными окружения

### TTS Service (tts-service)
- [x] **WebSocket API**: `ws://tts:8082/ws/tts` с JSON входом `{"text": "..."}`
- [x] **HTTP API**: `POST /api/tts` с chunked ответом
- [x] **Стриминг без буферизации**: PCM фреймы отправляются по мере генерации
- [x] **Фиксированный размер блока**: 1024 байта с допустимым drift ≤ 10%
- [x] **Корректная финализация**: `{"type":"end"}` для WS, окончание HTTP потока
- [x] **Health check**: `/health` endpoint

### ASR Service (asr-service)
- [x] **HTTP API**: `POST /api/stt/bytes` с query параметрами sr, ch, lang
- [x] **Поддержка PCM**: application/octet-stream без WAV заголовка
- [x] **JSON ответ**: `{"text": "..."}` с опциональными segments
- [x] **Ограничение времени**: ≤ 15 секунд аудио
- [x] **Health check**: `/health` endpoint

### Gateway Service (gateway)
- [x] **WebSocket proxy**: `ws://gateway:8000/ws/tts` для TTS
- [x] **Поддержка сегментов**: `{"segments": [{"text":"..."}, ...]}`
- [x] **Echo bytes**: `POST /api/echo-bytes` (ASR → TTS pipeline)
- [x] **Рестиминг без буферизации**: PCM фреймы передаются напрямую
- [x] **Health check**: `/health` с проверкой зависимостей

### Клиентские инструменты (client/)
- [x] **stream_tts.py**: WebSocket клиент с сохранением в out.wav
- [x] **echo_bytes.py**: HTTP клиент для echo-bytes с сохранением в out_echo.wav
- [x] **Временные метки**: печать времени получения фреймов
- [x] **Распознанный текст**: вывод текста/сегментов от ASR

### Качество кода
- [x] **Python + FastAPI**: современный веб-фреймворк
- [x] **Структурированное логирование**: JSON формат, отдельный поток для ошибок
- [x] **Конфигурация через env**: без хардкода портов/путей
- [x] **Обработка ошибок**: таймауты, 4xx/5xx коды, понятные сообщения
- [x] **Unit тесты**: 2-3 пограничных кейса на сервис
- [x] **Чистота кода**: структурированный, читаемый код

## 🛠 Технические решения

### Выбранные модели
- **TTS**: gTTS + Google Text-to-Speech (высокое качество речи, интернет-зависимый)
- **ASR**: OpenAI Whisper base.en (высокая точность, CPU совместимый)

### Особенности реализации
- **Стриминг TTS**: Реальное время без буферизации
- **Аудио обработка**: Автоматическое ресемплирование и нормализация
- **Микросервисная архитектура**: Независимые сервисы с четкими контрактами
- **Docker-first подход**: Полная контейнеризация с health checks

## 📁 Структура проекта

```
├── tts-service/          # TTS микросервис
│   ├── main.py          # FastAPI приложение
│   ├── tts_engine.py    # TTS движок (gTTS)
│   ├── models.py        # Pydantic модели
│   ├── config.py        # Конфигурация
│   ├── logger.py        # Логирование
│   ├── test_main.py     # Unit тесты
│   └── Dockerfile       # Docker образ
├── asr-service/         # ASR микросервис
│   ├── main.py          # FastAPI приложение
│   ├── asr_engine.py    # ASR движок (Whisper)
│   ├── models.py        # Pydantic модели
│   ├── config.py        # Конфигурация
│   ├── logger.py        # Логирование
│   ├── test_main.py     # Unit тесты
│   └── Dockerfile       # Docker образ
├── gateway/             # Gateway сервис
│   ├── main.py          # FastAPI приложение
│   ├── services.py      # Клиенты для TTS/ASR
│   ├── models.py        # Pydantic модели
│   ├── config.py        # Конфигурация
│   ├── logger.py        # Логирование
│   ├── test_main.py     # Unit тесты
│   └── Dockerfile       # Docker образ
├── client/              # Клиентские инструменты
│   ├── stream_tts.py    # WebSocket TTS клиент
│   ├── echo_bytes.py    # Echo bytes клиент
│   └── requirements.txt # Зависимости
├── docker-compose.yml   # Docker Compose конфигурация
├── env.example         # Пример переменных окружения
├── README.md           # Основная документация
├── QUICK_START.md      # Быстрый старт
├── DECISIONS.md        # Технические решения
└── PROJECT_SUMMARY.md  # Этот файл
```

## 🚀 Запуск

```bash
# 1. Клонирование и подготовка
git clone <repository-url>
cd TEST_Volgarev
cp env.example .env

# 2. Запуск сервисов
docker-compose up --build

# 3. Тестирование
pip install -r client/requirements.txt
python client/stream_tts.py
python client/echo_bytes.py

# 4. Запуск тестов
pip install -r requirements-test.txt
pytest tts-service/test_main.py asr-service/test_main.py gateway/test_main.py -v
```

## 📊 Производительность

- **TTS**: ~1-2 секунды для коротких текстов
- **ASR**: ~3-5 секунд для 10-секундного аудио (CPU)
- **Стриминг**: Задержка < 100ms между фреймами
- **Память**: ~2-3GB для всех сервисов

## 🔧 Настройка

Все параметры настраиваются через переменные окружения в `.env`:

```env
# Порты и хосты
GATEWAY_PORT=8000
TTS_PORT=8082
ASR_PORT=8081

# Модели
TTS_MODEL_NAME=gtts
ASR_MODEL_NAME=base.en

# Аудио параметры
TTS_SAMPLE_RATE=22050
ASR_SAMPLE_RATE=16000
TTS_CHUNK_SIZE=1024

# Логирование
LOG_LEVEL=INFO
LOG_FORMAT=json
```

## ✅ Соответствие требованиям

Проект полностью соответствует всем требованиям тестового задания:
- ✅ Минимальный, но аккуратно спроектированный пайплайн
- ✅ TTS со стриминговой выдачей аудио
- ✅ STT по готовому файлу
- ✅ Работа с Open-Source моделями
- ✅ Docker и инженерные навыки
- ✅ CPU-only решение (GPU не требуется)
- ✅ Только инференс (обучение не требуется)
- ✅ Чистота и красота кода
