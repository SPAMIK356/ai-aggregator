from django.db import migrations, models


class Migration(migrations.Migration):

	dependencies = [
		("core", "0003_rename_core_outbox_created_9dfbd1_idx_core_outbox_created_afd1b7_idx"),
	]

	operations = [
		migrations.CreateModel(
			name="WebsiteSource",
			fields=[
				("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
				("created_at", models.DateTimeField(auto_now_add=True)),
				("updated_at", models.DateTimeField(auto_now=True)),
				("name", models.CharField(max_length=255)),
				("url", models.URLField(unique=True)),
				("is_active", models.BooleanField(default=True)),
				("list_selector", models.CharField(max_length=255)),
				("title_selector", models.CharField(max_length=255)),
				("url_selector", models.CharField(max_length=255)),
				("desc_selector", models.CharField(blank=True, max_length=255)),
			],
		),
	]


