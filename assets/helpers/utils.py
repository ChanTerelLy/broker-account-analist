import csv
from io import StringIO
from datetime import datetime as dt


def parse_file(csv_upload):
    file = csv_upload.read().decode('utf-8-sig')
    csv_data = csv.reader(StringIO(file), delimiter=';')
    data = []
    for row in csv_data:
        data.append(row)
    return data

async def chunks(lst, n):
    """Yield successive n-sized chunks from lst."""
    for i in range(0, len(lst), n):
        yield lst[i:i + n]

def dmYHM_to_date(date):
    return dt.strptime(date, "%d.%m.%Y %H:%M").date() if date else None

def to_camel_case(snake_str):
    components = snake_str.split('_')
    return components[0] + ''.join(x.title() for x in components[1:])