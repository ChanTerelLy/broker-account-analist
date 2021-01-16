import asyncio
import time

import functools
import urllib

from django.http import JsonResponse
from django.shortcuts import render
from django.views.generic import TemplateView, ListView

from .helpers.gmail_parser import generate_google_cred, get_gmail_reports
from .models import *
from .helpers.service import Moex, SberbankReport
import pandas as pd
from .forms import UploadFile, UploadTransferFile
# Create your views here.
from .helpers.utils import parse_file
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from google.auth.transport.requests import Request

from django.shortcuts import redirect
from django.http import HttpResponse

SCOPES = ['https://www.googleapis.com/auth/gmail.readonly']
def provides_credentials(func):
    @functools.wraps(func)
    def wraps(request):
        # If OAuth redirect response, get credentials
        flow = InstalledAppFlow.from_client_secrets_file(
            'credentials/credentials.json', SCOPES,
            redirect_uri="http://localhost/google-cred")

        existing_state = request.GET.get('state', None)
        current_path = request.path
        if existing_state:
            secure_uri = request.build_absolute_uri(
                ).replace('http', 'https')
            location_path = urllib.parse.urlparse(existing_state).path
            flow.fetch_token(
                authorization_response=secure_uri,
                state=existing_state
            )
            request.session['credentials'] = flow.credentials.to_json()
            if location_path == current_path:
                return func(request, flow.credentials)
            # Head back to location stored in state when
            # it is different from the configured redirect uri
            return redirect(existing_state)


        # Otherwise, retrieve credential from request session.
        stored_credentials = request.session.get('credentials', None)
        if not stored_credentials:
            # It's strongly recommended to encrypt state.
            # location is needed in state to remember it.
            location = request.build_absolute_uri()
            # Commence OAuth dance.
            auth_url, _ = flow.authorization_url(state=location)
            return redirect(auth_url)

        # Hydrate stored credentials.
        credentials = Credentials(**json.loads(stored_credentials))

        # If credential is expired, refresh it.
        if credentials.expired and credentials.refresh_token:
            credentials.refresh(Request())

        # Store JSON representation of credentials in session.
        request.session['credentials'] = credentials.to_json()

        return func(request, credentials=credentials)
    return wraps


def update_bounds(requests):
    moex = Moex()
    tax_free_bounds = moex.get_corp_bound_tax_free()
    corp_bounds = asyncio.run(moex.bounds())
    data = pd.merge(corp_bounds, tax_free_bounds, right_on='ISIN', left_on='SECID', how='left')
    CorpBound.objects.all().delete()
    for index, row in data.iterrows():
        tax_free = True if row['Эмитент'] else False
        #TODO:find out field match
        CorpBound.objects.create(
            name=row['EMITENTNAME'],
            isin=row['ISIN_x'],
            last_price=row['PRICE_RUB'],
            assessed_return=row['YIELDATWAP'],
            maturity_date=row['MATDATE'] or datetime.now(),
            coupon_date_return=row['MATDATE'],
            coupon_price=row['RTH1'],
            # capitalization=row[''],
            # coupon_duration=row[''],
            listing=row['LISTLEVEL'],
            # demand_volume=row[''],
            # duration=row[''],
            nkd=0,
            tax_free= tax_free,
        )
    return JsonResponse({'data': data.to_json()}, safe=False)


def assets(request):
    return render(request, 'assets/assets.html')

class PortfolioView(TemplateView):
    template_name = 'assets/portfolio.html'

class TransfersView(TemplateView):
    template_name = 'assets/transfers.html'

class DealsView(TemplateView):
    template_name = 'assets/deals.html'

class CorpBounView(ListView):
    template_name = 'assets/corp-bounds.html'
    model = CorpBound
    context_object_name = 'corp_bounds'
    paginate_by = 100

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['help_text'] = CorpBound.objects.first().help_text_map_table
        return context

@provides_credentials
def update_report_gmail(request, credentials):
    htmls = get_gmail_reports('4NDKP', credentials)
    for html in htmls:
        data = SberbankReport().parse_html(html)
        AccountReport.save_from_dict(data)
    return JsonResponse('{"fds": 123}')