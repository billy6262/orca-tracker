import os
import sys
import django

# Setup Django
sys.path.append('/app')
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'app.settings')
django.setup()

from data_pipeline.models import RawReport
from data_pipeline.email_processor import process_txt_files_from_nested_folders

def reprocess_march_2009():
    print("March 2009 Reprocessing Tool")
    print("=" * 40)
    
    # Check current status
    march_reports = RawReport.objects.filter(messageId__contains="txt_file_2009_March")
    print(f"Current database records for March 2009: {march_reports.count()}")
    
    if march_reports.count() > 0:
        response = input("Delete existing March 2009 records and reprocess? (y/N): ")
        if response.lower() != 'y':
            print("Cancelled.")
            return
        
        # Delete existing records
        deleted_count = march_reports.count()
        march_reports.delete()
        print(f"Deleted {deleted_count} existing records")
    
    # Reprocess the files
    print("Reprocessing March 2009 files...")
    process_txt_files_from_nested_folders(
        "/app/txt_reports", 
        move_processed=False,  # Don't move files
        year_filter=[2009],
        month_filter=["March"]
    )
    
    # Check results
    new_count = RawReport.objects.filter(messageId__contains="txt_file_2009_March").count()
    print(f"New database records for March 2009: {new_count}")
    print("Reprocessing complete!")

if __name__ == "__main__":
    reprocess_march_2009()
