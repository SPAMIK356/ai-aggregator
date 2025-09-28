from django.core.management.base import BaseCommand, CommandError

from core.models import TelegramChannel


class Command(BaseCommand):
	help = "Add Telegram channels by list. Accepts comma-separated --channels or --file with one username per line."

	def add_arguments(self, parser):
		parser.add_argument("--channels", help="Comma-separated list like @channel1,@channel2", default="")
		parser.add_argument("--file", help="Path to file with one username per line", default="")

	def handle(self, *args, **options):
		usernames = []
		channels_arg = options.get("channels") or ""
		file_arg = options.get("file") or ""
		if channels_arg:
			usernames.extend([u.strip() for u in channels_arg.split(",") if u.strip()])
		if file_arg:
			try:
				with open(file_arg, "r", encoding="utf-8") as f:
					for line in f:
						username = line.strip()
						if username:
							usernames.append(username)
			except OSError as exc:
				raise CommandError(str(exc))

		if not usernames:
			raise CommandError("No channels provided")

		added = 0
		for u in usernames:
			u = u if u.startswith("@") else f"@{u}"
			obj, created = TelegramChannel.objects.get_or_create(username=u)
			if created:
				added += 1
			self.stdout.write(f"{obj.username} — {'created' if created else 'exists'}")

		self.stdout.write(self.style.SUCCESS(f"Done. Added: {added}, total processed: {len(usernames)}"))


