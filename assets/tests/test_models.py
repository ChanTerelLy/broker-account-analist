from django.test import TestCase
from assets.models import *
from datetime import datetime as dt
import random as rnd

class AssetModelTest(TestCase):
    fixtures = ['account.json', 'user.json', 'deal.json']

    def setUp(self):
        self.user = User.objects.first()
        self.account = Account.objects.first()
        self.isins = ['GAZP', 'LSR', 29009, 'SBR']
        self.types = ['Покупка', 'Продажа']
        self.deal_base = {
            "number": 123456675,
            "conclusion_date": dt.now(),
            "settlement_date": dt.now(),
            "isin": self.isins[0],
            "type": self.types[0],
            "amount": 20,
            "price": 129.2,
            "nkd": 0.0,
            "volume": 2584.0,
            "currency": "RUB",
            "service_fee": 0.0
        }


    def test_user(self):
        self.assertEquals(1, self.user.id)
        self.assertEquals('test', self.user.username)

    def test_account(self):
        self.assertEqual('test', self.account.name)

    def test_deals(self):
        deal1 = Deal.objects.filter(number=3003323040).first()
        deal2 = Deal.objects.filter(number=2935889523).first()
        deal3 = Deal.objects.filter(number=3013040975).first()
        
        self.assertEqual(deal1.account, self.account)
        self.assertEqual(deal2.account, self.account)
        self.assertEqual(deal3.account, self.account)

        self.assertEqual(deal1.type, 'Покупка')
        self.assertEqual(deal2.type, 'Продажа')
        self.assertEqual(deal3.type, 'Покупка')

        self.assertEqual(deal1.isin, 'FXJP ETF')
        self.assertEqual(deal2.isin, 'FXJP')
        self.assertEqual(deal3.isin, 'LSNGP')

        self.assertEquals(len(Deal.objects.all()),3)

    def test_deal_save_from_list(self):
        deals = []
        map = Deal.help_text_map_resolver()
        for i in range(3):
            deal = self.deal_base
            deal['number'] = rnd.randint(1000000, 3000000)
            deal['isin'] = self.isins[rnd.randint(0, len(self.isins) - 1)]
            deal['type'] = self.types[rnd.randint(0, len(self.types) - 1)]
            deal = {map.get(index, 'undefined'): attr for index, attr in deal.items()}
            deal['Номер договора'] = self.account.name
            deals.append(deal)
        Deal.save_from_list(deals)
        self.assertEquals(len(Deal.objects.all()),6)

    def test_deal_get_avg_price(self):
        # TODO: add more realistic cases
        deals = Deal.objects.all()
        deal1 = Deal.get_avg_price(deals[0].isin, [self.account])
        deal2 = Deal.get_avg_price(deals[1].isin, [self.account])
        deal3 = Deal.get_avg_price(deals[2].isin, [self.account])
        self.assertEqual(deal1, 2321.0)
        self.assertEqual(deal2, -2329.0)
        self.assertEqual(deal3, 129.2)

