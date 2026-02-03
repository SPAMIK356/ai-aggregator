# Generated migration for telegram_sent_at field

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('core', '0023_parserconfig_daily_limits'),
    ]

    operations = [
        migrations.AddField(
            model_name='newsitem',
            name='telegram_sent_at',
            field=models.DateTimeField(blank=True, db_index=True, null=True),
        ),
        migrations.AddField(
            model_name='authorcolumn',
            name='telegram_sent_at',
            field=models.DateTimeField(blank=True, db_index=True, null=True),
        ),
    ]
