from django.db import migrations, models


class Migration(migrations.Migration):

	dependencies = [
		("core", "0004_websitesource"),
	]

	operations = [
		migrations.CreateModel(
			name="RewriterConfig",
			fields=[
				("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
				("created_at", models.DateTimeField(auto_now_add=True)),
				("updated_at", models.DateTimeField(auto_now=True)),
				("is_enabled", models.BooleanField(default=False)),
				("model", models.CharField(default="gpt-4o-mini", max_length=64)),
				("prompt", models.TextField(blank=True, help_text="System instructions for rewriting. Use placeholders like {title} {content}")),
				("max_output_tokens", models.PositiveIntegerField(default=2048)),
			],
		),
	]


