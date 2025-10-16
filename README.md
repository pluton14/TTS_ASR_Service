# Streaming TTS + Offline STT Pipeline

Минимальный, но аккуратно спроектированный пайплайн для синтеза речи со стриминговой выдачей аудио и распознавания речи по файлу.

## Архитектура

Проект состоит из трех микросервисов:

1. **tts-service** - сервис синтеза речи с стриминговой отдачей PCM (gTTS + Google Text-to-Speech)
2. **asr-service** - сервис распознавания речи по файлу (OpenAI Whisper)
3. **gateway** - единая точка входа, проксирующая запросы и объединяющая поток TTS

## Быстрый запуск

### Предварительные требования
- Docker & Docker Compose
- Python 3.8+ (для клиентских скриптов)
- Минимум 4GB RAM (для Whisper модели)

### Запуск сервисов

1. Клонируйте репозиторий:
```bash
git clone <repository-url>
cd TEST_Volgarev
```

2. Скопируйте файл конфигурации:
```bash
cp env.example .env
```

3. Запустите сервисы:
```bash
docker-compose up --build
```

**Примечание:** 
- Первый запуск может занять несколько минут из-за загрузки Whisper модели
- TTS сервис использует Google Text-to-Speech и требует интернет-соединения

4. Проверьте статус сервисов:
```bash
# Проверка Gateway
curl http://localhost:8000/health

# Проверка TTS сервиса
curl http://localhost:8082/health

# Проверка ASR сервиса
curl http://localhost:8081/health
```

### Тестирование

1. Установите зависимости для клиентских скриптов:
```bash
pip install -r client/requirements.txt
```

2. Тест TTS через WebSocket:
```bash
python client/stream_tts.py
```

3. Тест echo-bytes функциональности:
```bash
python client/echo_bytes.py
```

### Запуск тестов

```bash
# Установите тестовые зависимости
pip install -r requirements-test.txt

# Запустите тесты для всех сервисов
pytest tts-service/test_main.py -v
pytest asr-service/test_main.py -v
pytest gateway/test_main.py -v
```

## API Endpoints

### Gateway
- `ws://localhost:8000/ws/tts` - WebSocket для TTS
- `POST /api/echo-bytes` - HTTP для echo-bytes функциональности

### TTS Service
- `ws://localhost:8082/ws/tts` - WebSocket для синтеза речи
- `POST /api/tts` - HTTP для синтеза речи

### ASR Service
- `POST /api/stt/bytes` - HTTP для распознавания речи

## Требования

- Docker & Docker Compose
- Python 3.8+ (для клиентских скриптов)

## Структура проекта

```
├── tts-service/          # TTS микросервис
├── asr-service/          # ASR микросервис  
├── gateway/              # Gateway сервис
├── client/               # Клиентские инструменты
├── docker-compose.yml    # Docker Compose конфигурация
├── .env.example         # Пример переменных окружения
└── DECISIONS.md         # Технические решения
```
