# Generated by Django 3.1 on 2022-01-05 21:35

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('assets', '0019_auto_20211102_1649'),
    ]

    operations = [
        migrations.AlterField(
            model_name='deal',
            name='number',
            field=models.CharField(help_text='Номер сделки', max_length=50, unique=True),
        ),
        migrations.AlterField(
            model_name='deal',
            name='price_rub',
            field=models.FloatField(default=0, help_text='Цена в рублях'),
        ),
        migrations.AlterField(
            model_name='transfer',
            name='sum_rub',
            field=models.FloatField(default=0, help_text='Сумма в рублях'),
        ),
    ]