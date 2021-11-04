from django.core.management.base import BaseCommand
from assets.models import Deal, Transfer


class Command(BaseCommand):
    help = 'refresh_deals_transfers'

    def handle(self, *args, **options):
        for deal in Deal.objects.all():
            deal.save()

        for transfer in Transfer.objects.all():
            transfer.save()
