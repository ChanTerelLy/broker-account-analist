# Generated by Django 3.1 on 2021-02-27 13:35

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('assets', '0005_account_broker_id'),
    ]

    operations = [
        migrations.AddField(
            model_name='accountreport',
            name='transfers',
            field=models.JSONField(default={}, help_text='Движение денежных средств за период'),
            preserve_default=False,
        ),
        migrations.AlterField(
            model_name='accountreport',
            name='asset_estimate',
            field=models.JSONField(help_text='Оценка активов'),
        ),
        migrations.AlterField(
            model_name='accountreport',
            name='end_date',
            field=models.DateField(help_text='Дата конца отчета'),
        ),
        migrations.AlterField(
            model_name='accountreport',
            name='handbook',
            field=models.JSONField(help_text='Справочник Ценных Бумаг'),
        ),
        migrations.AlterField(
            model_name='accountreport',
            name='iis_income',
            field=models.JSONField(help_text='Информация о зачислениях денежных средств на ИИС'),
        ),
        migrations.AlterField(
            model_name='accountreport',
            name='money_flow',
            field=models.JSONField(help_text='Денежные средства'),
        ),
        migrations.AlterField(
            model_name='accountreport',
            name='portfolio',
            field=models.JSONField(help_text='Портфель Ценных Бумаг'),
        ),
        migrations.AlterField(
            model_name='accountreport',
            name='start_date',
            field=models.DateField(help_text='Дата начала отчета'),
        ),
        migrations.AlterField(
            model_name='accountreport',
            name='tax',
            field=models.JSONField(help_text='Расчет и удержание налога'),
        ),
    ]