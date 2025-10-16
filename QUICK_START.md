# Руководство по быстрому запуску

## Быстрый запуск для тестирования

### 1. Подготовка
```bash
# Клонируйте репозиторий
git clone <repository-url>
cd TEST_Volgarev

# Скопируйте конфигурацию
cp env.example .env
```

### 2. Запуск сервисов
```bash
# Запустите все сервисы
docker-compose up --build

# В отдельном терминале проверьте статус
curl http://localhost:8000/health
```

### 3. Тестирование TTS
```bash
# Установите зависимости
pip install -r client/requirements.txt

# Тест WebSocket TTS
python client/stream_tts.py
# Введите текст или нажмите Enter для использования по умолчанию
# Результат сохранится в out.wav
```

### 4. Тестирование Echo Bytes
```bash
# Тест ASR -> TTS pipeline
python client/echo_bytes.py
# Скрипт создаст input.wav (тестовый тон) если файла нет
# Результат сохранится в out_echo.wav
```

### 5. Запуск тестов
```bash
# Установите тестовые зависимости
pip install -r requirements-test.txt

# Запустите все тесты
pytest tts-service/test_main.py asr-service/test_main.py gateway/test_main.py -v
```

## Решение проблем

### Проблема: Сервисы не запускаются
```bash
# Проверьте логи
docker-compose logs tts-service
docker-compose logs asr-service
docker-compose logs gateway

# Перезапустите с пересборкой
docker-compose down
docker-compose up --build
```

### Проблема: Медленная работа ASR
- Модель Whisper загружается при первом запуске
- Для ускорения можно использовать tiny.en вместо base.en
- Измените в .env: `ASR_MODEL_NAME=tiny.en`

### Проблема: Ошибки с аудио
- Убедитесь, что input.wav существует для echo_bytes.py
- Проверьте формат аудио (16kHz, моно рекомендуется)
- Для тестирования используйте WAV файлы

## API Тестирование

### WebSocket TTS
```bash
# Подключение через wscat (если установлен)
wscat -c ws://localhost:8000/ws/tts
# Отправьте: {"text": "Hello world"}
```

### HTTP Echo Bytes
```bash
# Тест с curl
curl -X POST "http://localhost:8000/api/echo-bytes?sr=16000&ch=1" \
  -H "Content-Type: application/octet-stream" \
  --data-binary @input.wav \
  --output out_echo.wav
```

### Прямой доступ к сервисам

#### TTS Service
```bash
# HTTP TTS
curl -X POST "http://localhost:8082/api/tts" \
  -H "Content-Type: application/json" \
  -d '{"text": "Hello world"}' \
  --output tts_output.wav
```

#### ASR Service
```bash
# STT
curl -X POST "http://localhost:8081/api/stt/bytes?sr=16000&ch=1" \
  -H "Content-Type: application/octet-stream" \
  --data-binary @input.wav
```

## Мониторинг

### Проверка здоровья сервисов
```bash
# Все сервисы
curl http://localhost:8000/health
curl http://localhost:8082/health  
curl http://localhost:8081/health

# Docker статус
docker-compose ps
```

### Логи
```bash
# Все логи
docker-compose logs -f

# Конкретный сервис
docker-compose logs -f tts-service
docker-compose logs -f asr-service
docker-compose logs -f gateway
```

## Остановка
```bash
# Остановить сервисы
docker-compose down

# Удалить volumes (модели и логи)
docker-compose down -v
```