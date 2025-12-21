from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('appointments', '0003_alter_appointment_total_price'),
    ]

    operations = [
        migrations.AddField(
            model_name='appointment',
            name='paid_amount',
            field=models.DecimalField(blank=True, decimal_places=2, max_digits=10, null=True, verbose_name='Оплаченная сумма'),
        ),
        migrations.AddField(
            model_name='appointment',
            name='paid_at',
            field=models.DateTimeField(blank=True, null=True, verbose_name='Оплачено в'),
        ),
        migrations.AddField(
            model_name='appointment',
            name='payment_id',
            field=models.CharField(blank=True, max_length=128, verbose_name='ID оплаты у провайдера'),
        ),
        migrations.AddField(
            model_name='appointment',
            name='payment_meta',
            field=models.JSONField(blank=True, default=dict, verbose_name='Детали оплаты (meta)'),
        ),
        migrations.AddField(
            model_name='appointment',
            name='payment_provider',
            field=models.CharField(blank=True, max_length=64, verbose_name='Провайдер оплаты'),
        ),
        migrations.AddField(
            model_name='appointment',
            name='payment_status',
            field=models.CharField(choices=[('pending', 'Ожидает оплаты'), ('paid', 'Оплачено'), ('failed', 'Ошибка оплаты'), ('refunded', 'Возврат')], default='pending', max_length=16, verbose_name='Статус оплаты'),
        ),
    ]


