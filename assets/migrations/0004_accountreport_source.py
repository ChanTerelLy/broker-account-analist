# Generated by Django 3.1 on 2021-01-26 09:34

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('assets', '0003_auto_20210125_1627'),
    ]

    operations = [
        migrations.AddField(
            model_name='accountreport',
            name='source',
            field=models.CharField(choices=[('sberbank', 'sberbank'), ('tinkoff', 'tinkoff')], default='sberbank', max_length=50),
            preserve_default=False,
        ),
    ]
