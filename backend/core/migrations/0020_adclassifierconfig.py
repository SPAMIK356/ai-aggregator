from django.db import migrations, models


class Migration(migrations.Migration):

	dependencies = [
		("core", "0019_linkfilter"),
	]

	operations = [
		migrations.CreateModel(
			name="AdClassifierConfig",
			fields=[
				("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
				("created_at", models.DateTimeField(auto_now_add=True)),
				("updated_at", models.DateTimeField(auto_now=True)),
				("is_enabled", models.BooleanField(default=False)),
				("model", models.CharField(max_length=64, default="gpt-4o-mini")),
				("prompt", models.TextField(
					blank=True,
					help_text="System instructions for classifying if content is an ad. Must return JSON with key 'is_ad': true or false.",
				)),
			],
		),
	]


