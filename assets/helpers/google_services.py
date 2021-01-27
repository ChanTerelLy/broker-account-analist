from __future__ import print_function

import io
import pickle
import os.path
import base64
from typing import Optional

import dateutil
from django.conf import settings
from django.urls import reverse
from google.api import http_pb2
from googleapiclient.discovery import build, Resource
from google.oauth2.credentials import Credentials
from google.oauth2 import credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from google.auth.transport.requests import Request
from django.shortcuts import redirect
import functools
import urllib
import json

from googleapiclient.http import MediaIoBaseDownload
from graphql.execution.tests.utils import resolved

from accounts.models import Profile
from assets.helpers.utils import xstr

SCOPES = ['https://www.googleapis.com/auth/gmail.readonly', 'https://www.googleapis.com/auth/drive.readonly']


def get_gmail_reports(credentials: Credentials, account_name: Optional[str] = None, max_page=10, limit=2000) -> list:
    """Return list of string what contain html pages with sberbank reports"""
    service = build('gmail', 'v1', credentials=credentials)
    # Call the Gmail API
    q = f'subject: SBERBANK. Brokerage report ' + xstr(account_name)
    results = service.users().messages().list(userId='me', q=q).execute()
    messages = results.get('messages', [])
    next_page = results.get('nextPageToken')
    if next_page and max_page > 1:  # get messages for other pages
        messages.extend(get_all_messages(service, next_page, q=q, limit=limit))

    htmls = []

    for message in messages[:limit]:
        #  Fetch attachments, try to find .html and decode from base64 to string
        message_body = service.users().messages().get(userId='me', id=message['id']).execute()
        attachments = message_body.get('payload', {}).get('parts', [])
        attach_id = None
        for attach in attachments:
            if '.html' in attach['filename']:
                attach_id = attach['body']['attachmentId']
                break
        if attach_id:
            data = service.users().messages().attachments().get(userId='me', messageId=message['id'],
                                                                id=attach_id).execute()
            data = data.get('data', None)
            if data:
                try:
                    html = base64.urlsafe_b64decode(data).decode(encoding='UTF-8', errors='ignore')
                    htmls.append(html)
                except Exception as e:
                    print(e)
                    continue

    return htmls


def get_all_messages(service: Resource, next_page: str, q: str, limit: int) -> list:
    """Looping through messages and nextPageToken until end of limit or batch of message is over"""
    messages = []
    while (next_page and len(messages) < limit):
        results = service.users().messages().list(userId='me', q=q, pageToken=next_page).execute()
        messages.extend(results.get('messages', []))
        next_page = results.get('nextPageToken')
    return messages

def get_money_manager_database(credentials: Credentials, user_id):
    service = build('drive', 'v3', credentials=credentials)
    folder = service.files().list(q="mimeType = 'application/vnd.google-apps.folder' and name = 'MoneyManager'").execute()
    folder = folder.get('files', [False])[0]
    if folder:
        q = f"'{folder['id']}' in parents"
        last_backup = service.files().list(q=q, orderBy='modifiedTime desc').execute()
        last_backup = last_backup.get('files', [None])[0]
        if last_backup:
            file = download_file(service, last_backup['id'], user_id)
            return {'file': file}
        else:
            return {'error': 'Backup files not founded'}
    else:
        return {'error': 'MoneyManager folder not founded '}


def download_file(service, file_id, user_id):
    """Download a Drive file's content to the local filesystem.
  
    Args:
      service: Drive API Service instance.
      file_id: ID of the Drive file that will downloaded.
    """
    file_name = f'tmp/db_user_{user_id}.mmbak'
    local_fd = io.FileIO(file_name, 'wb')
    request = service.files().get_media(fileId=file_id)
    media_request = MediaIoBaseDownload(local_fd, request)
    while True:
        try:
            download_progress, done = media_request.next_chunk()
        except Exception as e:
            print(e)
            return False
        if download_progress:
            print('Download Progress: %d%%' % int(download_progress.progress() * 100))
        if done:
            print('Download Complete')
            return file_name



def generate_google_cred_local() -> Credentials:
    """Return google Credentials (token.pickle), only for local or development usage"""
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
    """Wrap function return oath link for grant permission or get data from session if user already granted permissions"""
    @functools.wraps(func)
    def wraps(request, *args, **kwargs):
        # If OAuth redirect response, get credentials
        if not request:
            request = args[0].context
        if not request.user.is_authenticated:
            return {'success': False, 'redirect_uri': resolved('login')}
        flow = InstalledAppFlow.from_client_config(
            json.loads(settings.GOOGLE_CONFIG), SCOPES,
            redirect_uri=settings.GOOGLE_SERVICE_REDIRECT_URI)

        existing_state = request.GET.get('state', None)
        current_path = request.path
        if existing_state:
            secure_uri = request.build_absolute_uri(
            ).replace('http://', 'https://')
            location_path = urllib.parse.urlparse(existing_state).path
            flow.fetch_token(
                authorization_response=secure_uri,
                state=existing_state
            )
            Profile.objects.update_or_create(user=request.user,defaults={'google_service_token': flow.credentials.to_json()})
            if location_path == current_path:
                return func(request, flow.credentials)
            # Head back to location stored in state when
            # it is different from the configured redirect uri
            return redirect(existing_state)

        # Otherwise, retrieve credential from request session.
        profile, _ = Profile.objects.get_or_create(user=request.user)
        stored_credentials = profile.google_service_token
        if not stored_credentials:
            # It's strongly recommended to encrypt state.
            # location is needed in state to remember it.
            location = request.build_absolute_uri(reverse('home'))
            # Commence OAuth dance.
            auth_url, _ = flow.authorization_url(state=location)
            return {'success': False, 'redirect_uri': auth_url}

        # Hydrate stored credentials.
        cr = json.loads(stored_credentials)
        cr['expiry'] = dateutil.parser.isoparse(cr['expiry']).replace(tzinfo=None)
        credentials = Credentials(**cr)

        # If credential is expired, refresh it.
        if credentials.expired and credentials.refresh_token:
            credentials.refresh(Request())

        # Store JSON representation of credentials in session.
        Profile.objects.update_or_create(user=request.user, defaults={'google_service_token': credentials.to_json()})
        kwargs['credentials'] = credentials.to_json()

        return func(args[0], *args, **kwargs)

    return wraps
