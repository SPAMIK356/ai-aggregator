# AI Aggregator (MVP)

Minimal, production-leaning content platform focused on AI/Crypto news:
- News feed (automatic parsing from RSS/Atom and HTML websites)
- Author columns (manual posts via Django Admin)
- Telegram bot that periodically posts website news to a channel (images, full text, HTML formatting, optional AI rewriter)

### Tech Stack
- Backend: Django 5 + DRF, Celery, PostgreSQL/SQLite, Redis
- Frontend: Next.js 14 (App Router), React 18
- Orchestration: Docker Compose (prod-friendly)

### Repository Layout
```
news aggregator/
  backend/
    ai_aggregator/                # Django + Celery settings
    core/                         # models, admin, API, signals, tasks
    manage.py
    requirements.txt
  frontend/
    app/                          # pages: /, /news, /columns, /contact
    package.json
    next.config.js
  docker-compose.yml              # postgres, redis, backend, worker, beat
```

## Quick Start (local, without Docker)
Requirements: Python 3.11/3.12, Node.js 18+, npm, Windows PowerShell.

1) Python dependencies
```powershell
cd "D:\Projects\news aggregator"
py -m venv .venv
& ".venv\Scripts\python.exe" -m pip install -r "news aggregator\backend\requirements.txt"
```

2) Migrations and bootstrap (admin + demo sources + one-time parsing)
```powershell
$env:USE_SQLITE = "1"
& ".venv\Scripts\python.exe" "news aggregator\backend\manage.py" migrate
& ".venv\Scripts\python.exe" "news aggregator\backend\manage.py" bootstrap_ai_aggregator `
  --admin-email admin@example.com --admin-username admin --admin-password admin12345
```

3) Run backend
```powershell
$env:USE_SQLITE = "1"
& ".venv\Scripts\python.exe" "news aggregator\backend\manage.py" runserver 0.0.0.0:8000
```

4) Run frontend (in another terminal)
```powershell
cd "D:\Projects\news aggregator\news aggregator\frontend"
npm install
npm run dev
```

Services:
- Site: http://localhost:3000
- API: http://localhost:8000/api
- Admin: http://localhost:8000/admin (login: admin / password: admin12345)

## Run with Docker Compose
Requires Docker Desktop.
```powershell
cd "D:/Projects/news aggregator"
docker compose up -d --build
```
This brings up:
- postgres:5432
- redis:6379
- backend (gunicorn) on 8000
- worker (celery)
- beat (celery beat)

Run initial Django commands:
```powershell
docker compose exec backend python manage.py migrate
docker compose exec backend python manage.py collectstatic --noinput
docker compose exec backend python manage.py createsuperuser
```

Environment can be overridden via `.env` and `docker-compose.yml`.

## API
- GET `/api/news/?page=1` — news list (paginated)
- GET `/api/columns/?page=1` — columns list (paginated)
- GET `/api/columns/:id/` — column details

DRF pagination keys: `results`, `next`, `previous`, `count`.

## Parsers
### RSS/Atom
- Managed in Admin: `/admin/core/newssource/`
- Deduplication by `original_url`
- Periodic task: `run_parser` (scheduled)

### HTML Websites
Parse by CSS selectors; results go to the same `NewsItem` feed.

Admin: `/admin/core/websitesource/` fields
- `name` — source display name
- `url` — root page with article list
- `list_selector` — article container (e.g., `.post`)
- `title_selector` — title inside container (e.g., `.post-title`)
- `url_selector` — link selector (e.g., `.post-title a`)
- `desc_selector` — optional short description selector (e.g., `.excerpt`)
- `is_active` — enable source

Manual run:
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

Scheduled: Celery beat runs `fetch_websites` every 15 minutes.

### Telegram Channels (ingest via Telethon)
If you also ingest from Telegram channels (optional):
1) Create Telegram API app at `https://my.telegram.org` (get `api_id`/`api_hash`).
2) Generate `TG_STRING_SESSION`:
```powershell
$env:USE_SQLITE = "1"
& ".venv\Scripts\python.exe" "news aggregator\backend\manage.py" generate_tg_string_session
```
3) Set environment variables:
```powershell
$env:TG_API_ID = "123456"
$env:TG_API_HASH = "your_hash"
$env:TG_STRING_SESSION = "1A..."  # from step 2
```
4) Add channels:
```powershell
$env:USE_SQLITE = "1"
& ".venv\Scripts\python.exe" "news aggregator\backend\manage.py" add_tg_channels --channels "@openai,@telegram"
```
5) Manual fetch:
```powershell
$env:USE_SQLITE = "1"
& ".venv\Scripts\python.exe" - << 'PY'
import os
os.environ['DJANGO_SETTINGS_MODULE']='ai_aggregator.settings'
os.environ['USE_SQLITE']='1'
os.environ['TG_API_ID']=os.environ.get('TG_API_ID','')
os.environ['TG_API_HASH']=os.environ.get('TG_API_HASH','')
os.environ['TG_STRING_SESSION']=os.environ.get('TG_STRING_SESSION','')
import django; django.setup()
from core.tasks import fetch_telegram_channels
print(fetch_telegram_channels())
PY
```

## Telegram Bot (posting to a channel)
The bot periodically posts latest website news to your Telegram channel.

Key behavior:
- Posts full text (title + body), without the original source link
- Skips items originating from Telegram (only website-originated news)
- Sends images when available: prefers local files, then downloads remote URLs to upload, and finally falls back to sending the URL
- Formats text using Telegram HTML subset (`parse_mode=HTML`) with `_to_telegram_html`; falls back to plain text if needed
- Checkpointing: uses a `tg_last_posted_id.txt` file to avoid reposting and seeds from current max id to avoid obsolete news on first run

Environment:
- `TELEGRAM_BOT_TOKEN` — BotFather token
- `TELEGRAM_CHANNEL` — `@channel_username` or numeric `-100...` id (bot must be an admin)

Celery tasks involved:
- `poll_and_post_latest_news` — polls latest website news every 2 minutes and posts to Telegram
- `deliver_outbox` — used for outbox/webhook integration (not required for the periodic bot)

Celery Beat schedule:
- `poll_and_post_latest_news` is scheduled every 2 minutes and routed to `default` queue

Troubleshooting:
- `BadRequest: Chat not found` — check `TELEGRAM_CHANNEL` value and ensure the bot is an admin
- No images — verify `MEDIA_ROOT` mapping and that worker has access to media files; remote image download/upload is attempted before URL fallback
- HTML visible as text — ensure `parse_mode=HTML` is used for message text; captions are short and must not contain broken HTML

## AI Rewriter (Website and Telegram)
The project includes an AI rewriter integrated with OpenAI API and a Telegram-specific rewriter.

Models:
- `RewriterConfig` — site-wide rewriter
- `TelegramRewriterConfig` — Telegram-specific prompt/model and on/off switch

Environment:
- `OPENAI_API_KEY` — required
- `OPENAI_BASE_URL` — optional (custom endpoint)
- Timeouts/backoff/attempts controlled via settings (same strategy for Telegram rewriter)

Behavior:
- Telegram rewriter uses `rewrite_article_tg(title, content)` to return `{title, content, [hashtags], [theme]}`
- Same retry/backoff pattern as the website rewriter; optional fallback model

## Outbox/Webhook (optional integration)
Signals create `OutboxEvent` on new content:
- `news.created` (for `NewsItem`)
- `column.created` (for `AuthorColumn`)

`deliver_outbox` can POST events to `WEBHOOK_URL` with a JSON payload. This is not required for the Telegram channel bot (which uses periodic polling) but remains available if you need webhooks.

## Backend Environment Variables
- `DEBUG` (1/0)
- `ALLOWED_HOSTS`
- `USE_SQLITE` (1 for local SQLite)
- `POSTGRES_DB`, `POSTGRES_USER`, `POSTGRES_PASSWORD`, `POSTGRES_HOST`, `POSTGRES_PORT`
- `CELERY_BROKER_URL`, `CELERY_RESULT_BACKEND` (Redis recommended)
- `TIME_ZONE` (default: UTC)
- `PAGE_SIZE` (default: 20)
- `CORS_ALLOW_ALL_ORIGINS` (1/0)
- `WEBHOOK_URL` (optional, for outbox)
- `TELEGRAM_BOT_TOKEN`, `TELEGRAM_CHANNEL`
- `OPENAI_API_KEY`, `OPENAI_BASE_URL` (optional)
- Optional Telethon ingest: `TG_API_ID`, `TG_API_HASH`, `TG_STRING_SESSION`

## Content Management
- Sources (RSS): `/admin/core/newssource/`
- Website sources (HTML): `/admin/core/websitesource/`
- News (read-only list): `/admin/core/newsitem/`
- Columns: `/admin/core/authorcolumn/`
- Telegram rewriter config: `/admin/core/telegramrewriterconfig/`

Rich text (`content_body`) supports HTML; you can integrate TinyMCE/CKEditor for production.

## Production
- Set `ALLOWED_HOSTS`, use HTTPS behind a reverse proxy
- Use PostgreSQL + Redis + Celery; scale workers
- Ensure the bot has permissions in the Telegram channel and the worker/beat are running
