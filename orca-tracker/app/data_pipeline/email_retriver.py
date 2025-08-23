import os
import logging
import base64
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from google.auth.transport.requests import Request
from googleapiclient.discovery import build
from .models import RawReport


logger = logging.getLogger(__name__)

SCOPES = ['https://www.googleapis.com/auth/gmail.readonly']

def get_gmail_service():
    creds = None
    # Look for credentials in the app directory
    BASE_DIR = os.path.dirname(os.path.dirname(os.path.dirname(__file__)))  # Go up to project root
    SECRETS_DIR = os.path.join(BASE_DIR, 'secrets')
    TOKEN_PATH = os.path.join(SECRETS_DIR, 'token.json')
    CREDS_PATH = os.path.join(SECRETS_DIR, 'credentials.json')
    
    # The file token.json stores the user's access and refresh tokens.
    if os.path.exists(TOKEN_PATH):
        creds = Credentials.from_authorized_user_file(TOKEN_PATH, SCOPES)
    # If there are no valid credentials, let the user log in.
    if not creds or not creds.valid:
        if creds and creds.expired and creds.refresh_token:
            creds.refresh(Request())
        else:
            flow = InstalledAppFlow.from_client_secrets_file(
                CREDS_PATH, SCOPES)
            creds = flow.run_local_server(port=8080, open_browser=False)
        # Save the credentials for the next run
        with open(TOKEN_PATH, 'w') as token:
            token.write(creds.to_json())
    service = build('gmail', 'v1', credentials=creds)
    return service

def get_emails():
    service = get_gmail_service()
    results = service.users().messages().list(
        userId='me',
        labelIds=['INBOX'],
        q='is:unread',
        maxResults=20 
    ).execute()
    messages = results.get('messages', [])
    for msg in messages:
        msg_detail = service.users().messages().get(userId='me', id=msg['id'], format='full').execute()
        headers = msg_detail['payload']['headers']
        subject = next((h['value'] for h in headers if h['name'] == 'Subject'), '')
        sender = next((h['value'] for h in headers if h['name'] == 'From'), '')
        body = ''
        # Get plain text body
        if 'parts' in msg_detail['payload']:
            for part in msg_detail['payload']['parts']:
                if part['mimeType'] == 'text/plain':
                    body = part['body'].get('data', '')
                    if body:
                        # Decode from base64
                        body = base64.urlsafe_b64decode(body.encode('utf-8')).decode('utf-8')
                    break
        else:
            if msg_detail['payload']['mimeType'] == 'text/plain':
                body = msg_detail['payload']['body'].get('data', '')
                if body:
                    # Decode from base64
                    body = base64.urlsafe_b64decode(body.encode('utf-8')).decode('utf-8')
        try:
            if not RawReport.objects.filter(messageId=msg['id']).exists(): # Check if the report already exists
                # Create a new RawReport instance
                RawReport.objects.create(
                    messageId=msg['id'],  # Store the message ID to avoid duplicates
                    subject=subject,
                    sender=sender,
                    body=body
                )
                logger.info(f"Saved email from {sender} with subject '{subject}' to database.")
        except Exception as e:
            logger.error(f"Error saving email to database: {e}")



