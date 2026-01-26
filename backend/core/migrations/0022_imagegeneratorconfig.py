from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('core', '0021_add_russian_fields'),
    ]

    operations = [
        migrations.CreateModel(
            name='ImageGeneratorConfig',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('updated_at', models.DateTimeField(auto_now=True)),
                ('is_enabled', models.BooleanField(default=False)),
                ('api_key', models.CharField(blank=True, help_text='fal-ai API key (FAL_KEY)', max_length=255)),
                ('model', models.CharField(default='fal-ai/fast-sdxl', help_text='Model to use (e.g. fal-ai/fast-sdxl, fal-ai/flux/schnell)', max_length=128)),
                ('prompt_template', models.TextField(blank=True, help_text="Prompt template for image generation. Use {title} and {content} as placeholders. Example: 'A professional news illustration for: {title}'")),
                ('negative_prompt', models.TextField(blank=True, help_text='Negative prompt to avoid unwanted elements in generated images')),
                ('aspect_ratio', models.CharField(choices=[('square', 'Square (1:1)'), ('landscape_16_9', 'Landscape (16:9)'), ('landscape_4_3', 'Landscape (4:3)'), ('portrait_16_9', 'Portrait (9:16)'), ('portrait_4_3', 'Portrait (3:4)')], default='landscape_16_9', help_text='Aspect ratio for generated images', max_length=32)),
                ('num_inference_steps', models.PositiveIntegerField(default=4, help_text='Number of inference steps (higher = better quality, slower)')),
            ],
            options={
                'abstract': False,
            },
        ),
    ]

