from django.core.management.base import BaseCommand
from assets.models import Deal, Transfer, AccountReport


class Command(BaseCommand):
    help = 'refresh_deals_transfers'

    def handle(self, *args, **options):
        for report in AccountReport.objects.all():
            deals = report.deals
            for deal in deals:
                deal['Номер договора'] = report.account.name
            Deal.save_from_list(deals)
