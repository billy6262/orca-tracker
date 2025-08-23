import os
from django.core.management.base import BaseCommand
from data_pipeline.email_processor import process_txt_files_from_nested_folders

class Command(BaseCommand):
    help = 'Process raw text reports from a folder'

    def add_arguments(self, parser):
        parser.add_argument(
            '--folder',
            type=str,
            help='Path to folder containing txt files (default: ../Raw_text_reports)',
            default='Raw_text_reports'
        )
        parser.add_argument(
            '--move-processed',
            action='store_true',
            help='Move processed files to processed subfolder',
            default=True
        )

    def handle(self, *args, **options):
        folder_path = options['folder']
        move_processed = options['move_processed']
        
        # Convert relative path to absolute path
        if not os.path.isabs(folder_path):
            # Get the project root directory (orca-tracker)
            current_dir = os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(__file__))))
            folder_path = os.path.join(current_dir, folder_path)
        
        self.stdout.write(f'Processing text reports from: {folder_path}')
        
        try:
            process_txt_files_from_nested_folders(folder_path, move_processed=move_processed)
            self.stdout.write(self.style.SUCCESS('Successfully processed text reports.'))
        except Exception as e:
            self.stdout.write(self.style.ERROR(f'Error processing text reports: {e}'))