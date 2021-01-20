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
            "created_at": dt.now(),
            "updated_at": dt.now(),
            "account": self.account.uuid,
            "number": rnd.randint(1000000, 3000000),
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

    def test_save_from_list(self):
        pass

