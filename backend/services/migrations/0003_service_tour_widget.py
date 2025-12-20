from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('services', '0002_alter_service_service_type'),
    ]

    operations = [
        migrations.AddField(
            model_name='service',
            name='tour_widget',
            field=models.TextField(blank=True, help_text='HTML-код виджета (например, GoGuide 360)', null=True, verbose_name='Виджет 360/iframe'),
        ),
    ]

