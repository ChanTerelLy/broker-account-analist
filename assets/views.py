import asyncio

from django.http import JsonResponse
from django.shortcuts import render
from .models import CorpBound
from .v1.service import Moex
import pandas as pd
# Create your views here.

def update_bounds(requests):
    moex = Moex()
    tax_free_bounds = moex.get_corp_bound_tax_free('12.09.2020')
    corp_bounds = asyncio.run(moex.bounds())
    print(tax_free_bounds.info())
    print(corp_bounds.info())
    data = pd.merge(corp_bounds, tax_free_bounds, right_on='ISIN', left_on='SECID')
    return JsonResponse({'data': data.to_json()}, safe=False)