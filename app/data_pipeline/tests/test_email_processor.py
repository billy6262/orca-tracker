from django.test import TestCase
from unittest.mock import patch, MagicMock, mock_open
import json
import os
import tempfile
import base64
from datetime import datetime
from ..email_processor import (
    _extract_sightings, _create_sighting, _coerce_int, _calc_derived_fields,
    process_unprocessed_reports, process_txt_files_from_folder
)
from ..models import RawReport, OrcaSighting

class EmailProcessorTests(TestCase):
    
    def setUp(self):
        """Set up test data"""
        self.test_raw_report = RawReport.objects.create(
            messageId="test_123",
            subject="Test Orca Sighting",
            sender="test@example.com",
            body="Test sighting report",
            processed=False
        )
    
    def test_coerce_int_valid(self):
        """Test _coerce_int with valid integers"""
        self.assertEqual(_coerce_int("5"), 5)
        self.assertEqual(_coerce_int(10), 10)
        self.assertEqual(_coerce_int("0"), 0)
    
    def test_coerce_int_invalid(self):
        """Test _coerce_int with invalid values"""
        self.assertIsNone(_coerce_int("abc"))
        self.assertIsNone(_coerce_int(None))
        self.assertIsNone(_coerce_int(""))
    
    def test_calc_derived_fields(self):
        """Test _calc_derived_fields extracts correct values"""
        test_dt = datetime(2024, 6, 15, 14, 30, 0)  # June 15, 2024, 2:30 PM, Saturday
        month, dow, hour = _calc_derived_fields(test_dt)
        
        self.assertEqual(month, 6)
        self.assertEqual(dow, 6)  # Saturday is 6 in isoweekday()
        self.assertEqual(hour, 14)
    
    @patch('data_pipeline.email_processor.get_openai_client')
    def test_extract_sightings_success(self, mock_get_client):
        """Test successful sighting extraction"""
        mock_client = MagicMock()
        mock_get_client.return_value = mock_client
        
        mock_response = MagicMock()
        mock_response.choices[0].message.content = json.dumps({
            "sightings": [
                {
                    "time": "2024-08-13T10:30:00Z",
                    "zone": "6",
                    "direction": "N",
                    "count": 8
                }
            ]
        })
        mock_client.chat.completions.create.return_value = mock_response
        
        result = _extract_sightings("Orca pod spotted at Lime Kiln")
        
        self.assertEqual(len(result), 1)
        self.assertEqual(result[0]["zone"], "6")
        self.assertEqual(result[0]["count"], 8)
    
    @patch('data_pipeline.email_processor.get_openai_client')
    def test_extract_sightings_empty_body(self, mock_get_client):
        """Test extraction with empty body"""
        result = _extract_sightings("")
        self.assertEqual(result, [])
        mock_get_client.assert_not_called()
    
    @patch('data_pipeline.email_processor.get_openai_client')
    def test_extract_sightings_api_error(self, mock_get_client):
        """Test extraction handles API errors gracefully"""
        mock_client = MagicMock()
        mock_get_client.return_value = mock_client
        mock_client.chat.completions.create.side_effect = Exception("API Error")
        
        result = _extract_sightings("Test body")
        self.assertEqual(result, [])
    
    @patch('data_pipeline.email_processor.logger')
    def test_create_sighting_success(self, mock_logger):
        """Test successful sighting creation"""
        sighting_data = {
            "time": "2024-08-13T10:30:00Z",
            "zone": "6",
            "direction": "N",
            "count": 8
        }
        
        initial_count = OrcaSighting.objects.count()
        
        _create_sighting(self.test_raw_report, sighting_data)
        
        self.assertEqual(OrcaSighting.objects.count(), initial_count + 1)
        
        sighting = OrcaSighting.objects.last()
        self.assertEqual(sighting.raw_report, self.test_raw_report)
        self.assertEqual(sighting.zone, "6")
        self.assertEqual(sighting.direction, "N")
        self.assertEqual(sighting.count, 8)
        self.assertEqual(sighting.month, 8)
    
    @patch('data_pipeline.email_processor.logger')
    def test_create_sighting_invalid_time(self, mock_logger):
        """Test sighting creation with invalid time"""
        sighting_data = {
            "time": "invalid-time",
            "zone": "6",
            "direction": "N",
            "count": 8
        }
        
        initial_count = OrcaSighting.objects.count()
        _create_sighting(self.test_raw_report, sighting_data)
        
        # Should not create sighting with invalid time
        self.assertEqual(OrcaSighting.objects.count(), initial_count)
        mock_logger.warning.assert_called()
    
    @patch('data_pipeline.email_processor.logger')
    def test_create_sighting_invalid_count(self, mock_logger):
        """Test sighting creation with invalid count"""
        sighting_data = {
            "time": "2024-08-13T10:30:00Z",
            "zone": "6",
            "direction": "N",
            "count": "invalid"
        }
        
        initial_count = OrcaSighting.objects.count()
        _create_sighting(self.test_raw_report, sighting_data)
        
        # Should not create sighting with invalid count
        self.assertEqual(OrcaSighting.objects.count(), initial_count)
    
    @patch('data_pipeline.email_processor._extract_sightings')
    @patch('data_pipeline.email_processor._create_sighting')
    def test_process_unprocessed_reports(self, mock_create_sighting, mock_extract):
        """Test processing unprocessed reports"""
        # Create another unprocessed report
        report2 = RawReport.objects.create(
            messageId="test_456",
            subject="Another Test",
            sender="test2@example.com",
            body="Another test body",
            processed=False
        )
        
        mock_extract.return_value = [
            {
                "time": "2024-08-13T10:30:00Z",
                "zone": "6",
                "direction": "N",
                "count": 5
            }
        ]
        
        process_unprocessed_reports(limit=10)
        
        # Check reports are marked as processed
        self.test_raw_report.refresh_from_db()
        report2.refresh_from_db()
        self.assertTrue(self.test_raw_report.processed)
        self.assertTrue(report2.processed)
        
        # Check that _create_sighting was called for each report
        self.assertEqual(mock_create_sighting.call_count, 2)
    
    def test_process_txt_files_from_folder_no_folder(self):
        """Test processing with non-existent folder"""
        with patch('data_pipeline.email_processor.logger') as mock_logger:
            process_txt_files_from_folder("/nonexistent/path")
            mock_logger.error.assert_called_with("Folder does not exist: /nonexistent/path")
    
    @patch('data_pipeline.email_processor._extract_sightings')
    @patch('data_pipeline.email_processor._create_sighting')
    @patch('os.listdir')
    @patch('os.path.exists')
    @patch('os.makedirs')
    @patch('os.rename')
    def test_process_txt_files_success(self, mock_rename, mock_makedirs, mock_exists, mock_listdir, mock_create_sighting, mock_extract):
        """Test successful txt file processing"""
        # Setup mocks
        def exists_side_effect(path):
            if "test_folder" in path and not "processed" in path:
                return True
            elif "processed" in path:
                return False  # processed folder doesn't exist initially
            return False
        
        mock_exists.side_effect = exists_side_effect
        mock_listdir.return_value = ["report1.txt", "report2.txt", "notxt.pdf"]
        
        mock_extract.return_value = [
            {
                "time": "2024-08-13T10:30:00Z",
                "zone": "6",
                "direction": "N",
                "count": 3
            }
        ]
        
        test_content = "Orcas spotted at Lime Kiln Point"
        
        with patch('builtins.open', mock_open(read_data=test_content)):
            process_txt_files_from_folder("/test_folder", move_processed=True)
        
        # Check that RawReports were created (2 txt files)
        txt_reports = RawReport.objects.filter(messageId__startswith="txt_file_")
        self.assertEqual(txt_reports.count(), 2)
        
        # Check that _create_sighting was called for each file
        self.assertEqual(mock_create_sighting.call_count, 2)
        
        # Check that files were "moved" (renamed)
        self.assertEqual(mock_rename.call_count, 2)
    
    @patch('data_pipeline.email_processor._extract_sightings')
    @patch('os.listdir')
    @patch('os.path.exists')
    def test_process_txt_files_no_txt_files(self, mock_exists, mock_listdir, mock_extract):
        """Test processing folder with no .txt files"""
        mock_exists.return_value = True
        mock_listdir.return_value = ["file1.pdf", "file2.doc"]
        
        with patch('data_pipeline.email_processor.logger') as mock_logger:
            process_txt_files_from_folder("/test_folder")
            mock_logger.info.assert_called_with("No .txt files found in /test_folder")
    
    @patch('data_pipeline.email_processor._extract_sightings')
    @patch('os.listdir')
    @patch('os.path.exists')
    def test_process_txt_files_duplicate_skip(self, mock_exists, mock_listdir, mock_extract):
        """Test that duplicate txt files are skipped"""
        mock_exists.return_value = True
        mock_listdir.return_value = ["duplicate.txt"]
        
        # Create existing report with same messageId
        RawReport.objects.create(
            messageId="txt_file_duplicate",
            subject="Existing",
            sender="txt_file_import",
            body="existing content"
        )
        
        test_content = "New content"
        
        with patch('builtins.open', mock_open(read_data=test_content)):
            with patch('data_pipeline.email_processor.logger') as mock_logger:
                process_txt_files_from_folder("/test_folder")
                mock_logger.info.assert_called_with("File duplicate.txt already processed, skipping")
    
    @patch('data_pipeline.email_processor._extract_sightings')
    @patch('os.listdir')
    @patch('os.path.exists')
    def test_process_txt_files_file_error(self, mock_exists, mock_listdir, mock_extract):
        """Test handling of file read errors"""
        mock_exists.return_value = True
        mock_listdir.return_value = ["error.txt"]
        
        with patch('builtins.open', side_effect=IOError("File read error")):
            with patch('data_pipeline.email_processor.logger') as mock_logger:
                process_txt_files_from_folder("/test_folder")
                mock_logger.exception.assert_called()