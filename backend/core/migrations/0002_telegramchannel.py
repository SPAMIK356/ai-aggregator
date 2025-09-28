from django.db import migrations, models


class Migration(migrations.Migration):

	dependencies = [
		("core", "0001_initial"),
	]

	operations = [
		migrations.CreateModel(
			name="TelegramChannel",
			fields=[
				("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
				("created_at", models.DateTimeField(auto_now_add=True)),
				("updated_at", models.DateTimeField(auto_now=True)),
				("username", models.CharField(max_length=255, unique=True)),
				("title", models.CharField(blank=True, max_length=255)),
				("is_active", models.BooleanField(default=True)),
				("last_message_id", models.BigIntegerField(blank=True, null=True)),
			],
		),
	]




