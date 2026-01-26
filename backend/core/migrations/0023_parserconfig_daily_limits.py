from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('core', '0022_imagegeneratorconfig'),
    ]

    operations = [
        migrations.AddField(
            model_name='parserconfig',
            name='max_posts_per_day',
            field=models.PositiveIntegerField(default=0, help_text='Maximum total posts per day across all sources (0 = unlimited)'),
        ),
        migrations.AddField(
            model_name='parserconfig',
            name='max_posts_per_source_per_day',
            field=models.PositiveIntegerField(default=0, help_text='Maximum posts per individual source per day (0 = unlimited)'),
        ),
    ]

