from django.db import migrations, models


class Migration(migrations.Migration):

	dependencies = [
		("core", "0006_newsitem_image_url"),
	]

	operations = [
		migrations.AddField(
			model_name='websitesource',
			name='image_selector',
			field=models.CharField(max_length=255, blank=True),
		),
	]


