from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('business_units', '0012_businessunit_portal_theme'),
    ]

    operations = [
        migrations.AddField(
            model_name='businessunit',
            name='payout_account',
            field=models.CharField(blank=True, max_length=32, verbose_name='Расчетный счет / карта для выплат'),
        ),
        migrations.AddField(
            model_name='businessunit',
            name='payout_bank',
            field=models.CharField(blank=True, max_length=128, verbose_name='Банк для выплат'),
        ),
        migrations.AddField(
            model_name='businessunit',
            name='payout_bik',
            field=models.CharField(blank=True, max_length=16, verbose_name='БИК'),
        ),
        migrations.AddField(
            model_name='businessunit',
            name='payout_inn',
            field=models.CharField(blank=True, max_length=16, verbose_name='ИНН'),
        ),
        migrations.AddField(
            model_name='businessunit',
            name='payout_kpp',
            field=models.CharField(blank=True, max_length=16, verbose_name='КПП'),
        ),
        migrations.AddField(
            model_name='businessunit',
            name='payout_method',
            field=models.CharField(choices=[('bank', 'Банковский счет'), ('sbp', 'СБП / карта')], default='bank', max_length=16, verbose_name='Способ выплат'),
        ),
        migrations.AddField(
            model_name='businessunit',
            name='payout_name',
            field=models.CharField(blank=True, max_length=255, verbose_name='Юр. наименование / ФИО получателя'),
        ),
    ]


