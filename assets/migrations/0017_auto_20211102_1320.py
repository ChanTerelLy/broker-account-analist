# Generated by Django 3.1 on 2021-11-02 10:20

from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('assets', '0016_accountreport_deals'),
    ]

    operations = [
        migrations.RenameModel(
            old_name='Portfolio',
            new_name='MoexPortfolio',
        ),
        migrations.AlterModelTable(
            name='moexportfolio',
            table='assets_moex_portfolio',
        ),
    ]
