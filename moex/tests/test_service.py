import asyncio
import unittest

from moex.service import Cbr, Moex


class CbrTest(unittest.TestCase):

    def setUp(self) -> None:
        self.cbr = Cbr('01.01.2021')

    def test_usd(self):
        self.assertEqual(self.cbr.USD, 73.88)

    def test_euro(self):
        self.assertEqual(self.cbr.EUR, 90.79)


class MoexTest(unittest.TestCase):

    def setUp(self) -> None:
        self.loop = asyncio.get_event_loop()

    def test_not_contain_empty_list(self):
        data = self.loop.run_until_complete(Moex().get_shares('etf', ['RU000A100JH0', 'RU0009029540', 'IE00BD3QFB18']))
        for d in data:
            self.assertTrue(d)

    def test_bonds_tsqb(self):
        data = self.loop.run_until_complete(Moex().get_shares('bonds', ['RU000A100JH0']))
        self.assertEqual(data[0][0], 'RU000A100JH0')
        self.assertEqual(data[0][1], 'RU000A100JH0')

    def test_bonds_tqir(self):
        data = self.loop.run_until_complete(Moex().get_shares('bonds', ['RU000A1015P6']))
        self.assertEqual(data[0][0], 'RU000A1015P6')
        self.assertEqual(data[0][1], 'RU000A1015P6')


    def test_etf(self):
        data = self.loop.run_until_complete(Moex().get_shares('etf', ['IE00BD3QFB18', 'US0231351067']))
        self.assertEqual(data[0][0], 'IE00BD3QFB18')
        self.assertEqual(data[0][1], 'FXCN')

    def test_foreignshares(self):
        data = self.loop.run_until_complete(Moex().get_shares('foreignshares', ['US0231351067']))
        self.assertEqual(data[0][0], 'US0231351067')
        self.assertEqual(data[0][1], 'AMZN-RM')

    def test_shares(self):
        data = self.loop.run_until_complete(Moex().get_shares('shares', ['RU0009029540']))
        self.assertEqual(data[0][0], 'RU0009029540')
        self.assertEqual(data[0][1], 'SBER')

    def test_coupons_tsqb(self):
        data = self.loop.run_until_complete(Moex().get_coupon_by_isins(['RU000A100JH0']))
        self.assertEqual(data[0][0]['isin'], 'RU000A100JH0')

    def test_coupons_tqir(self):
        data = self.loop.run_until_complete(Moex().get_coupon_by_isins(['RU000A1015P6']))
        self.assertEqual(data[0][0]['isin'], 'RU000A1015P6')

if __name__ == '__main__':
    unittest.main()