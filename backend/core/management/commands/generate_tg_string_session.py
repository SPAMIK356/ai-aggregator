from django.core.management.base import BaseCommand, CommandError

try:
	from telethon.sync import TelegramClient
	from telethon.sessions import StringSession
except Exception as exc:  # pragma: no cover
	TelegramClient = None
	StringSession = None


class Command(BaseCommand):
	help = "Interactive: generate Telethon StringSession (uses TG_API_ID and TG_API_HASH env or prompts)."

	def handle(self, *args, **options):
		if TelegramClient is None:
			raise CommandError("Telethon not installed")
		import os
		api_id = os.getenv("TG_API_ID") or input("TG_API_ID: ")
		api_hash = os.getenv("TG_API_HASH") or input("TG_API_HASH: ")
		print("Follow the login steps in Telegram...")
		with TelegramClient(StringSession(), int(api_id), str(api_hash)) as client:
			string = client.session.save()
			print("\nYour TG_STRING_SESSION (keep it secret!):\n")
			print(string)
			print("\nSet it as environment variable TG_STRING_SESSION.")


