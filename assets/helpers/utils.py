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
    else:
        return None


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

    years = np.array(dates-dates[0], dtype='timedelta64[D]').astype(int)/365

    step = 0.05
    epsilon = 0.0001
    limit = 1000
    residual = 1

    #Test for direction of cashflows
    disc_val_1 = np.sum(amounts/((1+guess)**years))
    disc_val_2 = np.sum(amounts/((1.05+guess)**years))
    mul = 1 if disc_val_2 < disc_val_1 else -1

    #Calculate XIRR
    for i in range(limit):
        prev_residual = residual
        residual = np.sum(amounts/((1+guess)**years))
        if abs(residual) > epsilon:
            if np.sign(residual) != np.sign(prev_residual):
                step /= 2
            guess = guess + step * np.sign(residual) * mul
        else:
            return guess
    return 0

def get_total_xirr_percent(percent: float, days: int) -> float:
    return (days * percent)/365
