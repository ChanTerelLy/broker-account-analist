import csv
import os
from io import StringIO
from datetime import datetime as dt
import pandas as pd


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
        return dt.strptime(date, "%d.%m.%Y %H:%M").date() if date else None
    else:
        return date

def to_camel_case(snake_str):
    components = snake_str.split('_')
    return components[0] + ''.join(x.title() for x in components[1:])