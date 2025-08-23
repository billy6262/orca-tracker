import os
import sys
import django

# Setup Django
sys.path.append('/app')
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'app.settings')
django.setup()

from data_pipeline.models import RawReport

def check_march_2009():
    base_path = "/app/txt_reports/2009/March"
    
    print(f"Checking March 2009 folder: {base_path}")
    print(f"Folder exists: {os.path.exists(base_path)}")
    
    if not os.path.exists(base_path):
        return
    
    # Check main folder
    main_files = []
    processed_folder = None
    
    for item in os.listdir(base_path):
        item_path = os.path.join(base_path, item)
        if os.path.isfile(item_path) and item.lower().endswith('.txt'):
            main_files.append(item)
        elif os.path.isdir(item_path) and item.lower() == "processed":
            processed_folder = item_path
    
    print(f"Files in main March folder: {len(main_files)}")
    if main_files:
        print(f"Sample files: {main_files[:5]}")
    
    # Check processed subfolder
    processed_files = []
    if processed_folder and os.path.exists(processed_folder):
        processed_files = [f for f in os.listdir(processed_folder) if f.lower().endswith('.txt')]
        print(f"Files in processed subfolder: {len(processed_files)}")
        if processed_files:
            print(f"Sample processed files: {processed_files[:5]}")
    
    # Check database records
    march_reports = RawReport.objects.filter(messageId__contains="txt_file_2009_March").count()
    print(f"Database records for March 2009: {march_reports}")
    
    # Check specific files in database
    if main_files:
        for filename in main_files[:3]:
            base_name = os.path.splitext(filename)[0]
            message_id = f"txt_file_2009_March_{base_name}"
            exists = RawReport.objects.filter(messageId=message_id).exists()
            print(f"File {filename} in DB: {exists}")
    
    if processed_files:
        print("\nChecking processed files in database:")
        for filename in processed_files[:3]:
            base_name = os.path.splitext(filename)[0]
            message_id = f"txt_file_2009_March_{base_name}"
            exists = RawReport.objects.filter(messageId=message_id).exists()
            print(f"Processed file {filename} in DB: {exists}")

if __name__ == "__main__":
    check_march_2009()