import asyncio
import codecs
import csv
import os
from io import StringIO
from datetime import datetime as dt
import pandas as pd
import pytz
from pandas import Timestamp


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


def dmYHM_to_date(date):
    if isinstance(date, str):
        return dt.strptime(date, "%d.%m.%Y %H:%M").replace(tzinfo=pytz.UTC) if date else None
    elif isinstance(date, Timestamp):
        return date.to_pydatetime().replace(tzinfo=pytz.UTC)
    elif isinstance(date, dt):
        return date
    else:
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

def timestamp_to_string(date):
    if isinstance(date, Timestamp):
        return date.strftime('%Y-%m-%d')
    elif isinstance(date, str):
        return date


def to_camel_case(snake_str):
    components = snake_str.split('_')
    return components[0] + ''.join(x.title() for x in components[1:])


import numpy as np


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


import re

MATCH_ALL = r'.*'


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


def safe_list_get(l, idx, default):
    try:
        return l[idx]
    except IndexError:
        return default

def exclude_keys(list, *args):
    new_list = []
    for dict in list:
        new_list.append({key:value for key, value in dict.items() if key not in args})
    return new_list


def asyncio_helper(func, *args, **kwargs):
    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)
    loop = asyncio.get_event_loop()
    result = loop.run_until_complete(func(*args, **kwargs))
    loop.close()
    return result

def weird_division(n, d):
    return n / d if d else 0