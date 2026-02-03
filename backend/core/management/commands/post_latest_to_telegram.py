from __future__ import annotations

from django.core.management.base import BaseCommand, CommandError
from django.conf import settings
from django.utils import timezone

from core.models import NewsItem

try:
	from telegram import Bot
except Exception:  # pragma: no cover - optional dependency in some envs
	Bot = None


class Command(BaseCommand):
	help = "Send the latest news items to the configured Telegram channel via bot"

	def add_arguments(self, parser):
		parser.add_argument("--limit", type=int, default=5, help="How many latest news to send")
		parser.add_argument("--force", action="store_true", help="Send even if already sent (ignore telegram_sent_at)")

	def handle(self, *args, **options):
		bot_token = getattr(settings, "TELEGRAM_BOT_TOKEN", "")
		channel = getattr(settings, "TELEGRAM_CHANNEL", "")
		if not Bot:
			raise CommandError("python-telegram-bot is not installed")
		if not bot_token or not channel:
			raise CommandError("TELEGRAM_BOT_TOKEN and TELEGRAM_CHANNEL must be set in settings/env")

		limit = int(options.get("limit") or 5)
		force = options.get("force", False)
		
		# Only get items that haven't been sent yet (unless --force)
		qs = NewsItem.objects.order_by("-created_at")
		if not force:
			qs = qs.filter(telegram_sent_at__isnull=True)
		qs = qs[:max(1, limit)]
		
		if not qs:
			self.stdout.write(self.style.WARNING("No unsent news to send"))
			return

		bot = Bot(token=bot_token)
		sent = 0
		for n in qs:
			# Double-check telegram_sent_at (race condition protection)
			if not force and n.telegram_sent_at is not None:
				self.stdout.write(f"Skipping {n.id} - already sent at {n.telegram_sent_at}")
				continue
			
			title = (n.title or "New post").strip()
			link = (n.original_url or "").strip()
			msg = f"<b>{title}</b>\n{link}".strip()
			try:
				bot.send_message(chat_id=channel, text=msg, parse_mode="HTML", disable_web_page_preview=True)
				# Mark as sent
				n.telegram_sent_at = timezone.now()
				n.save(update_fields=["telegram_sent_at"])
				sent += 1
			except Exception as e:
				self.stdout.write(self.style.ERROR(f"Failed to send {n.id}: {e}"))
		self.stdout.write(self.style.SUCCESS(f"Sent {sent} messages to {channel}"))


