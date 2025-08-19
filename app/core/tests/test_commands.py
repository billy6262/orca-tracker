#unit tests for commands

from unittest.mock import patch

from psycopg2 import OperationalError as Pyscopg2Error

from django.core.management import call_command
from django.db.utils import OperationalError
from django.test import SimpleTestCase


@patch('core.management.commands.wait_for_db.Command.check')
class commandsTests(SimpleTestCase):

    def test_db_ready(self, patched_check):
        patched_check.return_value = True  # Simulate that the database is ready
        call_command('wait_for_db')
        patched_check.assert_called_once_with(databases=['default'])

    @patch('time.sleep')
    def test_db_not_ready(self ,patched_sleep ,patched_check):
        patched_check.side_effect = [Pyscopg2Error] * 5 + [OperationalError] * 5 + [True]
        # Simulate that the database is not ready for the first 10 attempts
        call_command('wait_for_db')
        self.assertEqual(patched_check.call_count, 11)
        patched_check.assert_called_with(databases=['default'])
    
