# Generated by Django 3.1 on 2021-01-26 22:32

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('assets', '0004_accountreport_source'),
    ]

    operations = [
        migrations.AddField(
            model_name='account',
            name='broker_id',
            field=models.CharField(blank=True, max_length=50, null=True),
        ),
    ]
