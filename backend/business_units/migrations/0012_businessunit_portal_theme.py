from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('business_units', '0011_businessunit_widget_config'),
    ]

    operations = [
        migrations.AddField(
            model_name='businessunit',
            name='portal_theme',
            field=models.CharField(default='dark', max_length=16, verbose_name='Тема портала (dark/light)'),
        ),
    ]


