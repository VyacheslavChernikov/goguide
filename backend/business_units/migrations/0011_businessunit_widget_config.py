from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('business_units', '0010_alter_businessunit_api_key'),
    ]

    operations = [
        migrations.AddField(
            model_name='businessunit',
            name='widget_config',
            field=models.JSONField(blank=True, default=dict, verbose_name='Настройки виджета бронирования'),
        ),
    ]

