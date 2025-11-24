import os

from celery import Celery
from celery.schedules import crontab


os.environ.setdefault("DJANGO_SETTINGS_MODULE", "ai_aggregator.settings")

app = Celery("ai_aggregator")
app.config_from_object("django.conf:settings", namespace="CELERY")
app.autodiscover_tasks()

app.conf.beat_schedule = {
	"run-parser-hourly": {
		"task": "core.tasks.run_parser",
		"schedule": crontab(minute=0, hour="*"),
	},
	"deliver-outbox-every-minute": {
		"task": "core.tasks.deliver_outbox",
		"schedule": crontab(minute="*"),
	},
	"fetch-telegram-every-5-min": {
		"task": "core.tasks.fetch_telegram_channels",
		"schedule": crontab(minute="*/5"),
	},
	"fetch-websites-every-15-min": {
		"task": "core.tasks.fetch_websites",
		"schedule": crontab(minute="*/15"),
	},
}


