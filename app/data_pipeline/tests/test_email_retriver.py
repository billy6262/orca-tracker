from django.test import TestCase
from unittest.mock import patch, MagicMock
import base64
from ..email_retriver import get_emails
from ..models import RawReport

class EmailRetrieverTests(TestCase):
    @patch('data_pipeline.email_retriver.get_gmail_service')
    def test_get_emails_saves_report(self, mock_get_gmail_service):
        # Mock Gmail service
        mock_service = MagicMock()
        mock_get_gmail_service.return_value = mock_service

        # Create a base64 encoded test body
        test_body = "Hello, this is a test email"
        encoded_body = base64.urlsafe_b64encode(test_body.encode('utf-8')).decode('utf-8')

        # Mock messages list response
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

        # Call the function
        get_emails()

        # Assert the messages list was called with correct parameters
        mock_service.users().messages().list.assert_called_with(
            userId='me',
            labelIds=['INBOX'],
            q='is:unread',
            maxResults=20
        )

        # Verify that a RawReport was created
        report = RawReport.objects.get(messageId='186e8b6b724b3e29')
        self.assertEqual(report.subject, 'Test Subject')
        self.assertEqual(report.sender, 'sender@example.com')
        self.assertEqual(report.body, test_body)

    @patch('data_pipeline.email_retriver.get_gmail_service')
    def test_get_emails_skips_duplicate(self, mock_get_gmail_service):
        # Create existing report
        RawReport.objects.create(
            messageId='186e8b6b724b3e29',
            subject='Existing Subject',
            sender='existing@example.com',
            body='Existing body'
        )

        # Mock Gmail service
        mock_service = MagicMock()
        mock_get_gmail_service.return_value = mock_service

        # Mock messages list response
        mock_service.users().messages().list.return_value.execute.return_value = {
            'messages': [{'id': '186e8b6b724b3e29'}]
        }

        # Mock message detail response
        mock_service.users().messages().get.return_value.execute.return_value = {
            'payload': {
                'headers': [
                    {'name': 'Subject', 'value': 'New Subject'},
                    {'name': 'From', 'value': 'new@example.com'}
                ],
                'mimeType': 'text/plain',
                'body': {'data': base64.urlsafe_b64encode(b"New body").decode('utf-8')}
            }
        }

        initial_count = RawReport.objects.count()

        # Call the function
        get_emails()

        # Assert no new report was created
        self.assertEqual(RawReport.objects.count(), initial_count)
        
        # Verify the original report is unchanged
        report = RawReport.objects.get(messageId='186e8b6b724b3e29')
        self.assertEqual(report.subject, 'Existing Subject')

    @patch('data_pipeline.email_retriver.get_gmail_service')
    def test_get_emails_handles_multipart_message(self, mock_get_gmail_service):
        """Test handling of multipart messages"""
        # Mock Gmail service
        mock_service = MagicMock()
        mock_get_gmail_service.return_value = mock_service

        test_body = "This is a multipart message"
        encoded_body = base64.urlsafe_b64encode(test_body.encode('utf-8')).decode('utf-8')

        # Mock messages list response
        mock_service.users().messages().list.return_value.execute.return_value = {
            'messages': [{'id': 'multipart_123'}]
        }

        # Mock multipart message detail response
        mock_service.users().messages().get.return_value.execute.return_value = {
            'payload': {
                'headers': [
                    {'name': 'Subject', 'value': 'Multipart Subject'},
                    {'name': 'From', 'value': 'multipart@example.com'}
                ],
                'parts': [
                    {
                        'mimeType': 'text/html',
                        'body': {'data': 'aHRtbCBib2R5'}  # HTML part
                    },
                    {
                        'mimeType': 'text/plain',
                        'body': {'data': encoded_body}  # Plain text part
                    }
                ]
            }
        }

        # Call the function
        get_emails()

        # Verify that the plain text part was extracted
        report = RawReport.objects.get(messageId='multipart_123')
        self.assertEqual(report.body, test_body)

    @patch('data_pipeline.email_retriver.get_gmail_service')
    def test_get_emails_handles_no_messages(self, mock_get_gmail_service):
        """Test handling when no unread messages exist"""
        # Mock Gmail service
        mock_service = MagicMock()
        mock_get_gmail_service.return_value = mock_service

        # Mock empty messages list response
        mock_service.users().messages().list.return_value.execute.return_value = {
            'messages': []
        }

        initial_count = RawReport.objects.count()

        # Call the function
        get_emails()

        # Assert no reports were created
        self.assertEqual(RawReport.objects.count(), initial_count)

    @patch('data_pipeline.email_retriver.get_gmail_service')
    def test_get_emails_handles_missing_headers(self, mock_get_gmail_service):
        """Test handling of messages with missing headers"""
        # Mock Gmail service
        mock_service = MagicMock()
        mock_get_gmail_service.return_value = mock_service

        test_body = "Message with missing headers"
        encoded_body = base64.urlsafe_b64encode(test_body.encode('utf-8')).decode('utf-8')

        # Mock messages list response
        mock_service.users().messages().list.return_value.execute.return_value = {
            'messages': [{'id': 'missing_headers_123'}]
        }

        # Mock message with missing Subject header
        mock_service.users().messages().get.return_value.execute.return_value = {
            'payload': {
                'headers': [
                    {'name': 'From', 'value': 'sender@example.com'}
                    # Subject header is missing
                ],
                'mimeType': 'text/plain',
                'body': {'data': encoded_body}
            }
        }

        # Call the function
        get_emails()

        # Verify that the report was created with empty subject
        report = RawReport.objects.get(messageId='missing_headers_123')
        self.assertEqual(report.subject, '')
        self.assertEqual(report.sender, 'sender@example.com')
        self.assertEqual(report.body, test_body)

    @patch('data_pipeline.email_retriver.get_gmail_service')
    def test_get_emails_handles_service_error(self, mock_get_gmail_service):
        """Test handling of Gmail service errors"""
        # Mock Gmail service to raise an exception
        mock_get_gmail_service.side_effect = Exception("Gmail API Error")

        # Call the function and expect it to raise the exception
        with self.assertRaises(Exception) as context:
            get_emails()
        
        # Verify the exception message
        self.assertIn("Gmail API Error", str(context.exception))