import csv
from io import StringIO


def parse_file(csv_upload):
    file = csv_upload.read().decode('utf-8')
    csv_data = csv.reader(StringIO(file), delimiter=';')
    data = []
    for row in csv_data:
        data.append(row)
    return data

async def chunks(lst, n):
    """Yield successive n-sized chunks from lst."""
    for i in range(0, len(lst), n):
        yield lst[i:i + n]