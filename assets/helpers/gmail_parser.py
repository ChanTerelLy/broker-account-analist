from __future__ import print_function
import pickle
import os.path

import base64
from googleapiclient.discovery import build
from google_auth_oauthlib.flow import InstalledAppFlow
from google.auth.transport.requests import Request

# If modifying these scopes, delete the file credentials/token.pickle.
SCOPES = ['https://www.googleapis.com/auth/gmail.readonly']

def get_gmail_reports(account_name, creds):
    # creds = generate_google_cred()

    service = build('gmail', 'v1', credentials=creds)

    # Call the Gmail API
    q = f'subject: {account_name}'
    results = service.users().messages().list(userId='me', q=q).execute()
    messages = results.get('messages', [])

    htmls = []

    for message in messages:
        message_body = service.users().messages().get(userId='me', id=message['id']).execute()
        attachments = message_body.get('payload', {}).get('parts', [])
        attach_id = None
        for attach in attachments:
            if '.html' in attach['filename']:
                attach_id = attach['body']['attachmentId']
                break
        if attach_id:
            data = service.users().messages().attachments().get(userId='me', messageId=message['id'], id=attach_id).execute()
            data = data.get('data', None)
            if data:
                try:
                    html = base64.urlsafe_b64decode(data).decode('utf-8')
                    htmls.append(html)
                except Exception as e:
                    print(e)
                    continue

    return htmls



def generate_google_cred():
    """Shows basic usage of the Gmail API.
    Lists the user's Gmail labels.
    """
    creds = None
    # The file credentials/token.pickle stores the user's access and refresh tokens, and is
    # created automatically when the authorization flow completes for the first
    # time.
    if os.path.exists('credentials/token.pickle'):
        with open('credentials/token.pickle', 'rb') as token:
            creds = pickle.load(token)
    # If there are no (valid) credentials available, let the user log in.
    if not creds or not creds.valid:
        if creds and creds.expired and creds.refresh_token:
            creds.refresh(Request())
        else:
            flow = InstalledAppFlow.from_client_secrets_file(
                'credentials/credentials.json', SCOPES)
            creds = flow.run_local_server(port=0)
        # Save the credentials for the next run
        with open('credentials/token.pickle', 'wb') as token:
            pickle.dump(creds, token)
    return creds