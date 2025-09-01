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

def _b64decode(s: str) -> str:
    if not s:
        return ''
    try:
        return base64.urlsafe_b64decode(s.encode('utf-8')).decode('utf-8', errors='replace')
    except Exception:
        try:
            return base64.urlsafe_b64decode((s + '===').encode('utf-8')).decode('utf-8', errors='replace')
        except Exception:
            return ''

def _fetch_attachment_text(service, msg_id: str, attachment_id: str) -> str:
    try:
        att = service.users().messages().attachments().get(userId='me', messageId=msg_id, id=attachment_id).execute()
        return _b64decode(att.get('data', ''))
    except Exception as e:
        logger.debug(f"Attachment fetch failed for {msg_id}:{attachment_id} - {e}")
        return ''

def _iter_text_parts(service, msg_id: str, payload):
    """Yield decoded text bodies for 'text/*' parts (recurses into multiparts)."""
    if not payload:
        return
    mime = payload.get('mimeType', '')
    if mime.startswith('multipart/'):
        for p in payload.get('parts', []) or []:
            yield from _iter_text_parts(service, msg_id, p)
        return
    if mime.startswith('text/'):
        body = payload.get('body', {}) or {}
        data = body.get('data')
        text = _b64decode(data) if data else ''
        if not text:
            att_id = body.get('attachmentId')
            if att_id:
                text = _fetch_attachment_text(service, msg_id, att_id)
        if text:
            yield text

def get_emails():
    service = get_gmail_service()
    res = service.users().messages().list(userId='me', labelIds=['INBOX'], q='is:unread', maxResults=20).execute()
    for msg in res.get('messages', []):
        detail = service.users().messages().get(userId='me', id=msg['id'], format='full').execute()
        headers = detail.get('payload', {}).get('headers', [])
        subject = next((h['value'] for h in headers if h['name'] == 'Subject'), '')
        sender = next((h['value'] for h in headers if h['name'] == 'From'), '')

        parts = list(_iter_text_parts(service, msg['id'], detail.get('payload', {})))
        # Fallback: single body if no parts
        if not parts:
            body = _b64decode(detail.get('payload', {}).get('body', {}).get('data', ''))
            if body:
                parts = [body]

        if not parts:
            logger.info(f"No text content for message {msg['id']} - skipped")
            continue

        for idx, body_text in enumerate(parts, start=1):
            part_msg_id = msg['id'] if idx == 1 else f"{msg['id']}pt{idx}"
            try:
                if not RawReport.objects.filter(messageId=part_msg_id).exists():
                    RawReport.objects.create(
                        messageId=part_msg_id,
                        subject=subject,
                        sender=sender,
                        body=body_text
                    )
                    logger.info(f"Saved {('part ' + str(idx)) if idx > 1 else 'message'} from {sender} | subject '{subject}' | id {part_msg_id}")
            except Exception as e:
                logger.error(f"Failed to save RawReport {part_msg_id}: {e}")



