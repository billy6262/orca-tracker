from django.test import TestCase
from unittest.mock import patch, MagicMock
import base64
from .email_retriver import get_emails

class EmailRetrieverTests(TestCase):
    @patch('data_pipeline.email_retriver.RawReport')
    @patch('data_pipeline.email_retriver.build')
    @patch('data_pipeline.email_retriver.Credentials')
    def test_get_emails_saves_report(self, mock_Credentials, mock_build, mock_RawReport):
        # Mock Gmail service
        mock_service = MagicMock()
        mock_build.return_value = mock_service

        # Create a base64 encoded test body
        test_body = "Hello, this is a test email"
        encoded_body = base64.urlsafe_b64encode(test_body.encode('utf-8')).decode('utf-8')

        # Mock messages list response with maxResults
        mock_service.users().messages().list.return_value.execute.return_value = {
            'messages': [{'id': '186e8b6b724b3e29'}]
        }

        # Mock message detail response
        mock_service.users().messages().get.return_value.execute.return_value = {
            'payload': {
                'headers': [
                    {'name': 'Subject', 'value': 'Test Subject'},
                    {'name': 'From', 'value': 'sender@example.com'}
                ],
                'mimeType': 'text/plain',
                'body': {'data': encoded_body}
            }
        }

        # Mock that the message hasn't been processed before
        mock_RawReport.objects.filter.return_value.exists.return_value = False

        # Call the function
        get_emails()

        # Assert the messages list was called with correct parameters
        mock_service.users().messages().list.assert_called_with(
            userId='me',
            labelIds=['INBOX'],
            q='is:unread',
            maxResults=20
        )

        # Assert RawReport.objects.create was called with correct parameters
        mock_RawReport.objects.create.assert_called_with(
            messageId='186e8b6b724b3e29',
            subject='Test Subject',
            sender='sender@example.com',
            body=test_body
        )

    @patch('data_pipeline.email_retriver.RawReport')
    @patch('data_pipeline.email_retriver.build')
    @patch('data_pipeline.email_retriver.Credentials')
    def test_get_emails_skips_duplicate(self, mock_Credentials, mock_build, mock_RawReport):
        # Mock Gmail service
        mock_service = MagicMock()
        mock_build.return_value = mock_service

        # Mock messages list response
        mock_service.users().messages().list.return_value.execute.return_value = {
            'messages': [{'id': '186e8b6b724b3e29'}]
        }

        # Mock that the message has already been processed
        mock_RawReport.objects.filter.return_value.exists.return_value = True

        # Call the function
        get_emails()

        # Assert create was not called
        mock_RawReport.objects.create.assert_not_called()
