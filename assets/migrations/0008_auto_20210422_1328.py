# Generated by Django 3.1 on 2021-04-22 10:28

import datetime
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('assets', '0007_auto_20210227_1755'),
    ]

    operations = [
        migrations.AddField(
            model_name='accountreport',
            name='created_at',
            field=models.DateTimeField(auto_now_add=True, default=datetime.datetime(2021, 4, 22, 13, 28, 9, 523796)),
            preserve_default=False,
        ),
        migrations.AddField(
            model_name='accountreport',
            name='updated_at',
            field=models.DateTimeField(auto_now=True),
        ),
        migrations.AlterField(
            model_name='accountreport',
            name='transfers',
            field=models.JSONField(default=dict, help_text='Движение денежных средств за период'),
        ),
    ]
