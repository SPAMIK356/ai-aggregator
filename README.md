# AI‑Aggregator (MVP)

Минимально жизнеспособная контент‑платформа на тему ИИ:
- Лента новостей (автоматический парсинг из источников RSS/Atom)
- Авторские колонки (ручные публикации через админку)
- Событийный «хук» для интеграции Telegram‑бота (outbox + webhook)

## Технологии
- Backend: Django 5 + DRF, Celery, PostgreSQL/SQLite, Redis
- Frontend: Next.js 14 (App Router), React 18
- Оркестрация: Docker Compose (опционально для прод)

## Структура
```
news aggregator/
  backend/
    ai_aggregator/                # настройки Django + Celery
    core/                         # модели, admin, API, сигналы, таски
    manage.py
    requirements.txt
  frontend/
    app/                          # страницы: /, /news, /columns, /contact
    package.json
    next.config.js
  docker-compose.yml              # postgres, redis, backend, worker, beat
```

## Быстрый старт (локально, без Docker)
Требования: Python 3.11/3.12, Node.js 18+ и npm, Windows PowerShell.

1) Установка зависимостей Python
```powershell
cd "D:\Projects\news aggregator"
py -m venv .venv
& ".venv\Scripts\python.exe" -m pip install -r "news aggregator\backend\requirements.txt"
```

2) Миграции и демо‑данные (админ + источники RSS + разовый парсинг)
```powershell
$env:USE_SQLITE = "1"
& ".venv\Scripts\python.exe" "news aggregator\backend\manage.py" migrate
& ".venv\Scripts\python.exe" "news aggregator\backend\manage.py" bootstrap_ai_aggregator `
  --admin-email admin@example.com --admin-username admin --admin-password admin12345
```

3) Запуск backend
```powershell
$env:USE_SQLITE = "1"
& ".venv\Scripts\python.exe" "news aggregator\backend\manage.py" runserver 0.0.0.0:8000
```

4) Запуск frontend (в другом терминале)
```powershell
cd "D:\Projects\news aggregator\news aggregator\frontend"
npm install
npm run dev
```

Сервисы:
- Сайт: http://localhost:3000
- API: http://localhost:8000/api
- Админка: http://localhost:8000/admin (логин: admin, пароль: admin12345)

## Запуск через Docker Compose (опционально)
Требуется Docker + Docker Compose.
```bash
cd "D:/Projects/news aggregator"
docker compose up -d --build
```
Поднимутся:
- postgres:5432
- redis:6379
- backend (gunicorn) на 8000
- worker (celery)
- beat (celery beat)

Переменные окружения можно переопределять через `docker-compose.yml`.

## API
- GET `/api/news/?page=1` — новости (пагинация)
- GET `/api/columns/?page=1` — авторские колонки (пагинация)
- GET `/api/columns/:id/` — колонка целиком

Пагинация DRF: `results`, `next`, `previous`, `count`.

## Парсер (Aggregator)
- Планировщик: Celery beat (каждый час)
- Источники: `/admin/core/newssource/`
- Дедупликация: `original_url` уникален

Ручной запуск без Celery:
```powershell
$env:USE_SQLITE = "1"
& ".venv\Scripts\python.exe" - << 'PY'
import os
os.environ['DJANGO_SETTINGS_MODULE']='ai_aggregator.settings'
os.environ['USE_SQLITE']='1'
import django; django.setup()
from core.tasks import run_parser
print(run_parser())
PY
```

### Telegram‑каналы вместо RSS
1) Получите API‑ключи Telegram: `https://my.telegram.org` (App api_id/api_hash)
2) Сгенерируйте `***`:
```powershell
$env:USE_SQLITE = "1"
& ".venv\Scripts\python.exe" "news aggregator\backend\manage.py" generate_tg_string_session
```
3) Установите переменные окружения:
```powershell
$env:TG_API_ID = "123456"
$env:*** = "your_hash"
$env:*** = "1A..."  # из шага 2
```
4) Добавьте каналы:
```powershell
$env:USE_SQLITE = "1"
& ".venv\Scripts\python.exe" "news aggregator\backend\manage.py" add_tg_channels --channels "@openai,@telegram"
```
5) Запуск сбора постов вручную:
```powershell
$env:USE_SQLITE = "1"
& ".venv\Scripts\python.exe" - << 'PY'
import os
os.environ['DJANGO_SETTINGS_MODULE']='ai_aggregator.settings'
os.environ['USE_SQLITE']='1'
os.environ['TG_API_ID']=os.environ.get('TG_API_ID','')
os.environ['***']=os.environ.get('***','')
os.environ['***']=os.environ.get('***','')
import django; django.setup()
from core.tasks import fetch_telegram_channels
print(fetch_telegram_channels())
PY
```
В Docker‑режиме заполните переменные в `docker-compose.yml` и запустите `worker` и `beat`.

### Парсер веб‑сайтов (HTML)
Можно парсить сайты при помощи CSS‑селекторов, результат публикуется в ту же ленту новостей (`NewsItem`).

1) Добавьте источник в админке `/admin/core/websitesource/`:
   - `name`: имя источника (отображается как `source_name`)
   - `url`: корневая страница со списком статей
   - `list_selector`: селектор контейнера статьи (например, `.post`)
   - `title_selector`: селектор заголовка внутри контейнера (например, `.post-title`)
   - `url_selector`: селектор ссылки внутри контейнера (например, `.post-title a`)
   - `desc_selector` (необязательно): селектор краткого описания (например, `.excerpt`)
   - `is_active`: включить источник

2) Запуск вручную:
```powershell
$env:USE_SQLITE = "1"
& ".venv\Scripts\python.exe" - << 'PY'
import os
os.environ['DJANGO_SETTINGS_MODULE']='ai_aggregator.settings'
os.environ['USE_SQLITE']='1'
import django; django.setup()
from core.tasks import fetch_websites
print(fetch_websites())
PY
```

3) Автоматически: Celery beat выполняет задачу `fetch_websites` каждые 15 минут.

## Интеграция событий (hook для Telegram‑бота)
Сигналы создают записи `OutboxEvent` при добавлении контента:
- `news.created` (для `NewsItem`)
- `column.created` (для `AuthorColumn`)

Celery‑таск `deliver_outbox` отправляет POST на `WEBHOOK_URL`:
```json
{
  "event_type": "news.created",
  "payload": {"post_type": "news", "title": "...", "link": "https://..."}
}
```
Настройка:
```powershell
$env:WEBHOOK_URL = "http://localhost:9000/webhook"
```

## Переменные окружения (backend)
- `DEBUG` (1/0)
- `ALLOWED_HOSTS`
- `USE_SQLITE` (1 — использовать SQLite локально)
- `POSTGRES_DB`, `POSTGRES_USER`, `POSTGRES_PASSWORD`, `POSTGRES_HOST`, `POSTGRES_PORT`
- `TIME_ZONE` (UTC по умолчанию)
- `PAGE_SIZE` (20 по умолчанию)
- `CORS_ALLOW_ALL_ORIGINS` (1/0)
- `CELERY_BROKER_URL`, `CELERY_RESULT_BACKEND`
- `WEBHOOK_URL`

## Управление контентом
- Источники: `/admin/core/newssource/`
- Новости (read‑only): `/admin/core/newsitem/`
- Колонки: `/admin/core/authorcolumn/`

В `content_body` допускается HTML. Для продакшена можно подключить TinyMCE/CKEditor.

## Безопасность и прод
- Настройте `ALLOWED_HOSTS`, HTTPS и реверс‑прокси.
- Используйте PostgreSQL + Redis + Celery, масштабируйте worker’ы.
