from django.test import TestCase
from unittest.mock import patch, MagicMock, mock_open
from ..email_retriver import get_gmail_service

class GmailServiceTests(TestCase):
    
    @patch('os.path.exists')
    @patch('data_pipeline.email_retriver.Credentials.from_authorized_user_file')
    @patch('data_pipeline.email_retriver.build')
    def test_get_gmail_service_with_valid_token(self, mock_build, mock_from_file, mock_exists):
        """Test Gmail service creation with valid existing token"""
        # Mock file existence
        mock_exists.return_value = True
        
        # Mock valid credentials
        mock_creds = MagicMock()
        mock_creds.valid = True
        mock_from_file.return_value = mock_creds
        
        # Mock service build
        mock_service = MagicMock()
        mock_build.return_value = mock_service
        
        # Call function
        service = get_gmail_service()
        
        # Assertions
        self.assertEqual(service, mock_service)
        mock_build.assert_called_with('gmail', 'v1', credentials=mock_creds)
    
    @patch('os.path.exists')
    @patch('builtins.open', new_callable=mock_open)
    @patch('data_pipeline.email_retriver.Credentials.from_authorized_user_file')
    @patch('data_pipeline.email_retriver.InstalledAppFlow.from_client_secrets_file')
    @patch('data_pipeline.email_retriver.build')
    def test_get_gmail_service_with_expired_token(self, mock_build, mock_flow, mock_from_file, mock_file, mock_exists):
        """Test Gmail service creation with expired token that gets refreshed"""
        # Mock file existence
        mock_exists.side_effect = lambda path: 'token.json' in path
        
        # Mock expired credentials that can be refreshed
        mock_creds = MagicMock()
        mock_creds.valid = False
        mock_creds.expired = True
        mock_creds.refresh_token = "refresh_token"
        mock_from_file.return_value = mock_creds
        
        # Mock service build
        mock_service = MagicMock()
        mock_build.return_value = mock_service
        
        # Call function
        service = get_gmail_service()
        
        # Assertions
        mock_creds.refresh.assert_called()
        self.assertEqual(service, mock_service)
    
    @patch('os.path.exists')
    def test_get_gmail_service_missing_credentials_file(self, mock_exists):
        """Test Gmail service creation when credentials file is missing"""
        # Mock that token exists but credentials file doesn't
        def exists_side_effect(path):
            if 'token.json' in path:
                return True
            if 'credentials.json' in path:
                return False
            return False
        
        mock_exists.side_effect = exists_side_effect
        
        # Mock invalid credentials that need refresh but no credentials file
        with patch('data_pipeline.email_retriver.Credentials.from_authorized_user_file') as mock_from_file:
            mock_creds = MagicMock()
            mock_creds.valid = False
            mock_creds.expired = True
            mock_creds.refresh_token = None
            mock_from_file.return_value = mock_creds
            
            # Should raise FileNotFoundError
            with self.assertRaises(FileNotFoundError):
                get_gmail_service()