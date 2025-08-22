from django.test import TestCase
from unittest.mock import patch, MagicMock, mock_open
import json
import os
import tempfile
import base64
from datetime import datetime
from ..email_processor import (
    _extract_sightings, _create_sighting, _coerce_int, _calc_derived_fields,
    process_unprocessed_reports, process_txt_files_from_nested_folders
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


    @patch('data_pipeline.email_processor.read_file_with_encoding_detection')
    @patch('os.listdir')
    @patch('os.path.exists')
    @patch('os.path.isdir')
    @patch('os.path.isfile')
    def test_process_nested_folders_skips_processed(self, mock_isfile, mock_isdir, mock_exists, mock_listdir, mock_read_file):
        """Test that process_txt_files_from_nested_folders skips 'processed' folders"""
        # Setup mock filesystem structure
        def mock_listdir_side_effect(path):
            if path == "/test_folder":
                return ["2024"]
            elif path == "/test_folder/2024":
                return ["January", "February", "processed"]  # Should skip the 'processed' folder
            elif path == "/test_folder/2024/January":
                return ["2024_January_01.txt", "2024_January_02.txt"]
            elif path == "/test_folder/2024/February":
                return ["2024_February_01.txt"]
            elif path == "/test_folder/2024/processed":
                return ["old_file.txt"]  # This should be skipped
            return []
        
        def mock_isdir_side_effect(path):
            return "processed" in path or "January" in path or "February" in path or path.endswith("2024")
        
        def mock_isfile_side_effect(path):
            return path.endswith(".txt")
        
        mock_listdir.side_effect = mock_listdir_side_effect
        mock_isdir.side_effect = mock_isdir_side_effect  
        mock_isfile.side_effect = mock_isfile_side_effect
        mock_exists.return_value = True
        mock_read_file.return_value = "Test sighting content"
        
        with patch('data_pipeline.email_processor._extract_sightings', return_value=[]):
            with patch('data_pipeline.email_processor.logger') as mock_logger:
                process_txt_files_from_nested_folders("/test_folder", move_processed=False)
                
                # Verify that processed folder was detected and logged
                mock_logger.info.assert_any_call("Skipping 1 processed folder(s) in 2024: ['processed']")
                
                # Verify that only January and February files were processed (3 total files)
                # We should see processing messages for these months but not for processed folder
                processing_calls = [call for call in mock_logger.info.call_args_list 
                                  if "Processing 2024" in str(call)]
                self.assertTrue(any("January" in str(call) for call in processing_calls))
                self.assertTrue(any("February" in str(call) for call in processing_calls))