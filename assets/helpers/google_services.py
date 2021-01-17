from __future__ import print_function
import pickle
import os.path
import base64

from django.conf import settings
from googleapiclient.discovery import build
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from google.auth.transport.requests import Request
from django.shortcuts import redirect
import functools
import urllib
import json

# If modifying these scopes, delete the file credentials/token.pickle.
SCOPES = ['https://www.googleapis.com/auth/gmail.readonly']

def get_gmail_reports(account_name, credentials, max_page=10, limit=2000):
    # creds = generate_google_cred()

    service = build('gmail', 'v1', credentials=credentials)
    # Call the Gmail API
    q = f'subject: {account_name}'
    results = service.users().messages().list(userId='me', q=q).execute()
    messages = results.get('messages', [])
    next_page = results.get('nextPageToken')
    if next_page and max_page > 1:
        messages.extend(get_all_messages(service, next_page, q=q, limit=limit))

    htmls = []

    for message in messages[:limit]:
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
                    html = base64.urlsafe_b64decode(data).decode(encoding='UTF-8',errors='ignore')
                    htmls.append(html)
                except Exception as e:
                    print(e)
                    continue

    return htmls

def get_all_messages(service, next_page, q, limit):
    messages = []
    while(next_page and len(messages) < limit):
        results = service.users().messages().list(userId='me', q=q, pageToken=next_page).execute()
        messages.extend(results.get('messages', []))
        next_page = results.get('nextPageToken')
    return messages


def generate_google_cred_local():
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

def provides_credentials(func, *args, **kwargs):
    @functools.wraps(func)
    def wraps(request, *args, **kwargs):
        # If OAuth redirect response, get credentials
        if not request:
            request = args[0].context
        flow = InstalledAppFlow.from_client_config(
            json.loads(settings.GOOGLE_CONFIG), SCOPES,
            redirect_uri=settings.GOOGLE_SERVICE_REDIRECT_URI)

        existing_state = request.GET.get('state', None)
        current_path = request.path
        if existing_state:
            secure_uri = request.build_absolute_uri(
                )
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
            return {'success': False, 'redirect_uri': auth_url}

        # Hydrate stored credentials.
        cr = json.loads(stored_credentials)
        credentials = Credentials(
            token=cr['token'],
            refresh_token=cr['refresh_token'],
            token_uri=cr['token_uri'],
            client_id=cr['client_id'],
            client_secret=cr['client_secret'],
            scopes=cr['scopes'],
            # expiry=cr['expiry'], not working on google library (dateutil.parser.isoparse(cr['expiry']))
        )

        # If credential is expired, refresh it.
        if credentials.expired and credentials.refresh_token:
            credentials.refresh(Request())

        # Store JSON representation of credentials in session.
        request.session['credentials'] = credentials.to_json()
        kwargs['credentials'] = credentials.to_json()

        return func(args, kwargs)
    return wraps