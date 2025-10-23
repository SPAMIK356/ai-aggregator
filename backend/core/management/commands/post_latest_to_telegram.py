from __future__ import annotations

from django.core.management.base import BaseCommand, CommandError
from django.conf import settings

from core.models import NewsItem

try:
	from telegram import Bot
except Exception:  # pragma: no cover - optional dependency in some envs
	Bot = None


class Command(BaseCommand):
	help = "Send the latest news items to the configured Telegram channel via bot"

	def add_arguments(self, parser):
		parser.add_argument("--limit", type=int, default=5, help="How many latest news to send")

	def handle(self, *args, **options):
		bot_token = getattr(settings, "TELEGRAM_BOT_TOKEN", "")
		channel = getattr(settings, "TELEGRAM_CHANNEL", "")
		if not Bot:
			raise CommandError("python-telegram-bot is not installed")
		if not bot_token or not channel:
			raise CommandError("TELEGRAM_BOT_TOKEN and TELEGRAM_CHANNEL must be set in settings/env")

		limit = int(options.get("limit") or 5)
		qs = NewsItem.objects.order_by("-created_at")[:max(1, limit)]
		if not qs:
			self.stdout.write(self.style.WARNING("No news to send"))
			return

		bot = Bot(token=bot_token)
		sent = 0
		for n in qs:
			title = (n.title or "New post").strip()
			link = (n.original_url or "").strip()
			msg = f"<b>{title}</b>\n{link}".strip()
			bot.send_message(chat_id=channel, text=msg, parse_mode="HTML", disable_web_page_preview=True)
			sent += 1
		self.stdout.write(self.style.SUCCESS(f"Sent {sent} messages to {channel}"))


