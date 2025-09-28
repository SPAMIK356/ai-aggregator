from django.core.management.base import BaseCommand
from django.contrib.auth import get_user_model

from core.models import NewsSource
from core.tasks import run_parser


class Command(BaseCommand):
	help = "Create admin, seed sources, run parser once"

	def add_arguments(self, parser):
		parser.add_argument("--admin-email", default="admin@example.com")
		parser.add_argument("--admin-username", default="admin")
		parser.add_argument("--admin-password", default="admin12345")

	def handle(self, *args, **options):
		User = get_user_model()
		username = options["admin_username"]
		email = options["admin_email"]
		password = options["admin_password"]

		u, created = User.objects.get_or_create(
			username=username, defaults={"email": email}
		)
		if created:
			u.set_password(password)
			u.is_staff = True
			u.is_superuser = True
			u.save()
			self.stdout.write(self.style.SUCCESS("Admin user created"))
		else:
			self.stdout.write("Admin user exists")

		# Seed sources
		seed_urls = [
			("Habr AI", "https://habr.com/ru/rss/hub/machine_learning/"),
			("OpenAI Blog", "https://openai.com/blog/rss.xml"),
		]
		for name, url in seed_urls:
			obj, _ = NewsSource.objects.get_or_create(url=url, defaults={"title": name})
			self.stdout.write(f"Source: {obj}")

		# Run parser once
		result = run_parser()
		self.stdout.write(self.style.SUCCESS(f"Parser result: {result}"))


