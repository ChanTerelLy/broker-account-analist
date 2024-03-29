import asyncio
import codecs
import copy
import csv
import datetime
import os
from decimal import Decimal
from io import StringIO
from datetime import datetime as dt, timedelta
import pandas as pd
import pytz
from pandas import Timestamp
import re
import numpy as np

MATCH_ALL = r'.*'


def parse_file(uploaded_file):
    if uploaded_file.name.endswith('.csv'):
        file = uploaded_file.read().decode('utf-8-sig')
        csv_data = csv.reader(StringIO(file), delimiter=';')
        data = []
        for row in csv_data:
            data.append(row)
        data = list([dict(zip(data[0], c)) for c in data[1:]])
    elif uploaded_file.name.endswith('.xlsx'):
        data = pd.read_excel(uploaded_file).to_dict(orient='records')
    elif uploaded_file.name.endswith('.html'):
        data = uploaded_file.read()
    return data


async def chunks(lst, n):
    """Yield successive n-sized chunks from lst."""
    for i in range(0, len(lst), n):
        yield lst[i:i + n]


def timestamp_to_string(date):
    if isinstance(date, Timestamp):
        return date.strftime('%Y-%m-%d')
    elif isinstance(date, str):
        return date


def to_camel_case(snake_str):
    components = snake_str.split('_')
    return components[0] + ''.join(x.title() for x in components[1:])


def xirr(df, guess=0.05, date_column='execution_date', amount_column='sum'):
    '''Calculates XIRR from a series of cashflows.
       Needs a dataframe with columns date and amount, customisable through parameters.
       Requires Pandas, NumPy libraries'''

    df = df.sort_values(by=date_column).reset_index(drop=True)

    amounts = df[amount_column].values
    dates = df[date_column].values

    years = np.array(dates - dates[0], dtype='timedelta64[D]').astype(int) / 365

    step = 0.05
    epsilon = 0.0001
    limit = 100
    residual = 1

    # Test for direction of cashflows
    disc_val_1 = np.sum(amounts / ((1 + guess) ** years))
    disc_val_2 = np.sum(amounts / ((1.05 + guess) ** years))
    mul = 1 if disc_val_2 < disc_val_1 else -1

    # Calculate XIRR
    for i in range(limit):
        prev_residual = residual
        residual = np.sum(amounts / ((1 + guess) ** years))
        if abs(residual) > epsilon:
            if np.sign(residual) != np.sign(prev_residual):
                step /= 2
            guess = guess + step * np.sign(residual) * mul
        else:
            return guess
    return 0


def get_total_xirr_percent(percent: float, days: int) -> float:
    return (days * percent) / 365


def full_strip(text: str) -> str:
    text = ' '.join(text.split()).strip()
    return text


def like(string):
    """
    Return a compiled regular expression that matches the given
    string with any prefix and postfix, e.g. if string = "hello",
    the returned regex matches r".*hello.*"
    """
    string_ = string
    if not isinstance(string_, str):
        string_ = str(string_)
    regex = MATCH_ALL + re.escape(string_) + MATCH_ALL
    return re.compile(regex, flags=re.DOTALL)


def find_by_text(soup, text, tag, **kwargs):
    """
    Find the tag in soup that matches all provided kwargs, and contains the
    text.

    If no match is found, return None.
    If more than one match is found, raise ValueError.
    """
    elements = soup.find_all(tag, **kwargs)
    matches = []
    for element in elements:
        if element.find(text=like(text)):
            matches.append(element)
    if len(matches) > 1:
        raise ValueError("Too many matches:\n" + "\n".join(matches))
    elif len(matches) == 0:
        return None
    else:
        return matches[0]


def convert_devided_number(value):
    if isinstance(value, (int, float)):
        return value
    if isinstance(value, str):
        splited = value.split()
        value = ''.join(splited)
        try:
            value = float(value)
        except:
            pass
    return value


def asyncio_helper(func, *args, **kwargs):
    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)
    loop = asyncio.get_event_loop()
    result = loop.run_until_complete(func(*args, **kwargs))
    loop.close()
    return result


def weird_division(n, d):
    return n / d if d else 0


def conver_to_number(value):
    if not value:
        return 0
    if isinstance(value, (int, float, Decimal)):
        return abs(value)
    else:
        value = ''.join(value.split())
        return abs(float(value))


def get_value(obj):
    return None if not obj else obj.value


def xstr(s):
    if s is None:
        return ''
    return str(s)


def list_to_dict(list):
    return {k: v for element in list for k, v in element.items()}


def get_summed_values(accounts_with_sums):
    resulted_sums = {}
    for r in accounts_with_sums:
        acc_with_sums = {}
        for a in r['data']:
            if acc_with_sums.get(a.date):
                acc_with_sums[a.date]['sum'] = acc_with_sums[a.date]['sum'] if acc_with_sums[a.date].get('sum') else conver_to_number(
                    a.sum)
                acc_with_sums[a.date]['income_sum'] = acc_with_sums[a.date]['income_sum'] if acc_with_sums[a.date].get(
                    'income_sum') else conver_to_number(a.income_sum)
            else:
                acc_with_sums[a.date] = {'sum': a.sum, 'income_sum': a.income_sum}
        c_year = dt.now().year
        c_month = dt.now().month
        for _type in ['income_sum', 'sum']:
            previos_value = {'sum': 0, 'income_sum': 0}
            zero_value = {'sum': 0, 'income_sum': 0}
            for y in range(c_year - 2, c_year + 1):
                for m in range(1, 13):
                    if c_year == y and m > c_month:
                        break
                    fake_date = datetime.date(y, m, 1)
                    month_dates = [d for d in acc_with_sums.keys() if d.month == m and d.year == y and acc_with_sums[d].get(_type)]
                    last_date = max(month_dates) if month_dates else None
                    pv = previos_value.copy()
                    last_values = acc_with_sums[last_date].copy() if acc_with_sums.get(last_date) else None
                    if last_date and not resulted_sums.get(fake_date):
                        # create first record
                        resulted_sums[fake_date] = zero_value.copy()
                        resulted_sums[fake_date][_type] = acc_with_sums[last_date][_type]
                        previos_value[_type] = last_values[_type]
                    elif last_date and resulted_sums.get(fake_date):
                        # update existed record
                        if resulted_sums[fake_date][_type]:
                            resulted_sums[fake_date][_type] += conver_to_number(acc_with_sums[last_date][_type])
                        else:
                            resulted_sums[fake_date][_type] = conver_to_number(acc_with_sums[last_date][_type])
                        previos_value[_type] = last_values[_type]
                    elif not last_date and not resulted_sums.get(fake_date):
                        # set previous values for month if no other operation happens
                        resulted_sums[fake_date] = pv
                    else:
                        if resulted_sums[fake_date][_type]:
                            resulted_sums[fake_date][_type] += conver_to_number(pv[_type])
                        else:
                            resulted_sums[fake_date][_type] = conver_to_number(pv[_type])
    return resulted_sums


### DATE FUNCTIONS ###
def dt_to_date(d):
    if isinstance(d, dt):
        return d.date()
    else:
        return d


def dt_now():
    return dt.now()


def dt_year_before():
    return dt.now() - timedelta(days=365)


def dmYHM_to_date(date):
    try:
        if isinstance(date, str):
            return dt.strptime(date, "%d.%m.%Y %H:%M").replace(tzinfo=pytz.UTC) if date else None
        elif isinstance(date, Timestamp):
            return date.to_pydatetime().replace(tzinfo=pytz.UTC)
        elif isinstance(date, dt):
            return date
        else:
            return None
    except Exception as e:
        return None


def dmY_to_date(date):
    if isinstance(date, str):
        return dt.strptime(date, "%d.%m.%Y").replace(tzinfo=pytz.UTC) if date else None
    elif isinstance(date, Timestamp):
        return date.to_pydatetime().replace(tzinfo=pytz.UTC)
    else:
        return None


def dmY_hyphen_to_date(date):
    if isinstance(date, str):
        return dt.strptime(date, "%Y-%m-%d").replace(tzinfo=pytz.UTC) if date else None
    elif isinstance(date, Timestamp):
        return date.to_pydatetime().replace(tzinfo=pytz.UTC)
    else:
        return None


def date_to_dmY(dt):
    return dt.strftime("%d.%m.%Y")

def dt_tag():
    return dt.now().strftime('%Y_%m_%d_%H_%M')