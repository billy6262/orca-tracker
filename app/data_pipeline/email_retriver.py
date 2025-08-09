import email
import imaplib
import logging
from .models import RawReport

EmailPassword = 'aw4ergYUI%^Q@'
EmailName = 'dorchakorcareports@outlook.com'  #outlook email that recives orca reports

imap_url = 'outlook.office365.com'  #imap server for outlook

logger = logging.getLogger(__name__)

def get_emails():
    imap = imaplib.IMAP4_SSL(imap_url)
    imap.login(EmailName, EmailPassword)  #login to email server
    imap.select('INBOX')  #select inbox to read emails from
    status, messages = imap.search(None, 'UNSEEN')  #search for unseen emails
    email_ids = messages[0].split()  #list of email ids

    for email_id in email_ids:
        statuas, msg_data = imap.fetch(email_id, '(RFC822)')  #fetch the email by id

        for response_part in msg_data:
            if isinstance(response_part, tuple):
                body = ""
                msg = email.message_from_bytes(response_part[1])  #parse email bytes to email object

                subject, encoding = email.header.decode_header(msg['Subject'])[0]  #decode subject
                if isinstance(subject, bytes):  #if it's bytes, decode to str
                    subject = subject.decode(encoding)

                sender, encoding = email.header.decode_header(msg.get('From'))[0]  #decode from
                if isinstance(sender, bytes):
                    sender = sender.decode(encoding)

                if msg.is_multipart():  #if email is multipart
                    for part in msg.walk():  #walk through the parts
                        content_type = part.get_content_type()

                        if content_type == 'text/plain': #only process plain text parts skipping html and attachments
                            try:
                                body += part.get_payload(decode=True).decode()
                            except Exception as e:
                                logger.error(f"Error decoding email body: {e}")

                else:  #if email is not multipart
                    content_type = msg.get_content_type()

                    if content_type == 'text/plain':
                        try:
                            body = msg.get_payload(decode=True).decode()
                        except Exception as e:
                            logger.error(f"Error decoding email body: {e}")

                # Save the email content to the database
                try:
                    RawReport.objects.create(
                        subject=subject,
                        sender=sender,
                        body=body
                    )
                    logger.info(f"Saved email from {sender} with subject '{subject}' to database.")
                except Exception as e:
                    logger.error(f"Error saving email to database: {e}")

    imap.close()
    imap.logout()