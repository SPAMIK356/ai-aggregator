from django.db import migrations, models


class Migration(migrations.Migration):

	dependencies = [
		("core", "0017_telegramrewriterconfig"),
	]

	operations = [
		migrations.AlterField(
			model_name="hashtag",
			name="slug",
			field=models.SlugField(max_length=64),
		),
	]


