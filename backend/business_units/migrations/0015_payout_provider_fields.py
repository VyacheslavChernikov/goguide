from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('business_units', '0014_payoutrequest'),
    ]

    operations = [
        migrations.AddField(
            model_name='businessunit',
            name='payout_mode',
            field=models.CharField(choices=[('test', 'Тест'), ('live', 'Боевой')], default='test', max_length=8, verbose_name='Режим выплат'),
        ),
        migrations.AddField(
            model_name='businessunit',
            name='payout_provider',
            field=models.CharField(choices=[('manual', 'Ручной'), ('mock', 'Тестовый'), ('yookassa', 'YooKassa Payouts'), ('cloudpayments', 'CloudPayments Payouts'), ('tinkoff', 'Тинькофф Выплаты')], default='manual', max_length=32, verbose_name='Провайдер выплат'),
        ),
        migrations.AddField(
            model_name='businessunit',
            name='payout_provider_extra',
            field=models.JSONField(blank=True, default=dict, verbose_name='Доп. данные провайдера'),
        ),
        migrations.AddField(
            model_name='businessunit',
            name='payout_provider_key',
            field=models.CharField(blank=True, max_length=255, verbose_name='ID / Public / TerminalKey'),
        ),
        migrations.AddField(
            model_name='businessunit',
            name='payout_provider_secret',
            field=models.CharField(blank=True, max_length=255, verbose_name='Secret / API key'),
        ),
        migrations.AddField(
            model_name='businessunit',
            name='payout_webhook_secret',
            field=models.CharField(blank=True, max_length=255, verbose_name='Секрет для подписи вебхука'),
        ),
    ]


