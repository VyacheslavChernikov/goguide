from django.db import migrations, models
import django.db.models.deletion
from django.conf import settings


class Migration(migrations.Migration):

    dependencies = [
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
        ('business_units', '0013_payout_fields'),
    ]

    operations = [
        migrations.CreateModel(
            name='PayoutRequest',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('amount', models.DecimalField(decimal_places=2, max_digits=10, verbose_name='Сумма вывода')),
                ('fee', models.DecimalField(decimal_places=2, default=0, max_digits=10, verbose_name='Комиссия')),
                ('currency', models.CharField(default='RUB', max_length=3, verbose_name='Валюта')),
                ('status', models.CharField(choices=[('pending', 'На проверке'), ('processing', 'В обработке'), ('paid', 'Выплачено'), ('failed', 'Ошибка')], default='pending', max_length=16, verbose_name='Статус')),
                ('provider', models.CharField(choices=[('manual', 'Ручной'), ('mock', 'Тестовый'), ('yookassa', 'YooKassa Payouts'), ('cloudpayments', 'CloudPayments Payouts'), ('tinkoff', 'Тинькофф Выплаты')], default='manual', max_length=32, verbose_name='Провайдер')),
                ('provider_payout_id', models.CharField(blank=True, max_length=128, verbose_name='ID выплаты у провайдера')),
                ('meta', models.JSONField(blank=True, default=dict, verbose_name='Метаданные/ответ провайдера')),
                ('comment', models.TextField(blank=True, verbose_name='Комментарий')),
                ('created_at', models.DateTimeField(auto_now_add=True, verbose_name='Создано')),
                ('processed_at', models.DateTimeField(blank=True, null=True, verbose_name='Обработано')),
                ('business_unit', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='payouts', to='business_units.businessunit', verbose_name='Площадка')),
                ('requested_by', models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, to=settings.AUTH_USER_MODEL, verbose_name='Инициатор')),
            ],
            options={
                'verbose_name': 'Выплата',
                'verbose_name_plural': 'Выплаты',
                'ordering': ['-created_at'],
            },
        ),
    ]


