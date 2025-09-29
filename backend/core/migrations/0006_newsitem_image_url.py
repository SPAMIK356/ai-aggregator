from django.db import migrations, models


class Migration(migrations.Migration):

	dependencies = [
		("core", "0005_rewriterconfig"),
	]

	operations = [
		migrations.AddField(
			model_name='newsitem',
			name='image_url',
			field=models.CharField(max_length=1000, blank=True),
		),
	]


