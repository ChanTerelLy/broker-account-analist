from django.contrib.auth.models import User
from django.test import TestCase
from django.urls import reverse


class AssetsViewTest(TestCase):
    fixtures = ['user.json']

    def setUp(self):
        self.user = User.objects.first()

    def test_assets(self):
        response = self.client.get(reverse('assets'))
        self.assertEqual(response.status_code, 302)
        self.assertRedirects(response, reverse('login') + '?next=%2Fassets%2F')
        self.client.force_login(self.user)
        response = self.client.get(reverse('assets'))
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'assets/assets.html')
        self.assertContains(response, 'AVG доходность за год')
        self.assertContains(response, 'Доход за все время')

    def test_moex_portfolio(self):
        response = self.client.get(reverse('moex-portfolio'))
        self.assertEqual(response.status_code, 302)
        self.assertRedirects(response, reverse('login') + '?next=/moex-portfolio/')
        self.client.force_login(self.user)
        response = self.client.get(reverse('moex-portfolio'))
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'assets/moex-portfolio.html')

    def test_transfers(self):
        response = self.client.get(reverse('transfers'))
        self.assertEqual(response.status_code, 302)
        self.assertRedirects(response, reverse('login') + '?next=/transfers/')
        self.client.force_login(self.user)
        response = self.client.get(reverse('transfers'))
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'assets/transfers.html')

    def test_deals(self):
        response = self.client.get(reverse('deals'))
        self.assertEqual(response.status_code, 302)
        self.assertRedirects(response, reverse('login') + '?next=/deals/')
        self.client.force_login(self.user)
        response = self.client.get(reverse('deals'))
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'assets/deals.html')

    def test_report_portfolio(self):
        response = self.client.get(reverse('report-portfolio'))
        self.assertEqual(response.status_code, 302)
        self.assertRedirects(response, reverse('login') + '?next=/report-portfolio/')
        self.client.force_login(self.user)
        response = self.client.get(reverse('report-portfolio'))
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'assets/report-portfolio.html')

    def test_update_bounds(self):
        self.client.force_login(self.user)
        response = self.client.get(reverse('update-bounds'))
        self.assertEqual(response.status_code, 302)  # forbidden access except stuff users

    def test_corp_bounds(self):
        response = self.client.get(reverse('corp-bounds'))
        self.assertEqual(response.status_code, 302)
        self.assertRedirects(response, reverse('login') + '?next=/corp-bounds/')
        self.client.force_login(self.user)
        response = self.client.get(reverse('corp-bounds'))
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'assets/corp-bounds.html')
