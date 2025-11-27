from django.db import migrations, models


class Migration(migrations.Migration):

	dependencies = [
		("core", "0018_alter_hashtag_slug"),
	]

	operations = [
		migrations.CreateModel(
			name="LinkFilter",
			fields=[
				("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
				("created_at", models.DateTimeField(auto_now_add=True)),
				("updated_at", models.DateTimeField(auto_now=True)),
				("prefix", models.CharField(max_length=255, help_text="Prefix to match at the start of a link, e.g. '[Channel]https://t.me/'")),
				("is_active", models.BooleanField(default=True)),
			],
		),
	]


