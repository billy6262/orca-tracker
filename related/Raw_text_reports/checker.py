import os

def find_empty_folders(directory_path):
    """Find and report empty folders in the given directory."""
    empty_folders = []
    
    print(f"Checking for empty folders in: {directory_path}")
    print("=" * 60)
    
    # Walk through all directories
    for root, dirs, files in os.walk(directory_path):
        for dir_name in dirs:
            dir_path = os.path.join(root, dir_name)
            
            # Check if directory is empty (no files and no subdirectories with content)
            if is_directory_empty(dir_path):
                relative_path = os.path.relpath(dir_path, directory_path)
                empty_folders.append(relative_path)
    
    return empty_folders

def is_directory_empty(dir_path):
    """Check if a directory is completely empty (no files or non-empty subdirectories)."""
    try:
        # Get all items in the directory
        items = os.listdir(dir_path)
        
        # If no items, it's empty
        if not items:
            return True
        
        # Check if all items are empty directories
        for item in items:
            item_path = os.path.join(dir_path, item)
            if os.path.isfile(item_path):
                # Found a file, directory is not empty
                return False
            elif os.path.isdir(item_path):
                # If subdirectory is not empty, this directory is not empty
                if not is_directory_empty(item_path):
                    return False
        
        # All subdirectories are empty, so this directory is effectively empty
        return True
    
    except PermissionError:
        print(f"Permission denied: {dir_path}")
        return False
    except Exception as e:
        print(f"Error checking {dir_path}: {e}")
        return False

def get_folder_structure_summary(directory_path):
    """Get a summary of the folder structure."""
    total_folders = 0
    folders_with_files = 0
    total_files = 0
    
    for root, dirs, files in os.walk(directory_path):
        total_folders += len(dirs)
        if files:
            folders_with_files += 1
        total_files += len(files)
    
    return total_folders, folders_with_files, total_files

if __name__ == "__main__":
    # Set the directory to check (your orca tracker directory)
    base_directory = r"c:\Users\andre\OneDrive\Desktop\Web Dev\orca tracker\Raw_text_reports"
    
    # Check if directory exists
    if not os.path.exists(base_directory):
        print(f"Directory not found: {base_directory}")
        exit(1)
    
    # Get folder structure summary
    total_folders, folders_with_files, total_files = get_folder_structure_summary(base_directory)
    
    print(f"DIRECTORY ANALYSIS: {base_directory}")
    print("=" * 80)
    print(f"Total folders found: {total_folders}")
    print(f"Folders with files: {folders_with_files}")
    print(f"Total files found: {total_files}")
    print()
    
    # Find empty folders
    empty_folders = find_empty_folders(base_directory)
    
    if empty_folders:
        print(f"EMPTY FOLDERS FOUND ({len(empty_folders)}):")
        print("-" * 40)
        
        # Group by year for better organization
        by_year = {}
        for folder in empty_folders:
            parts = folder.split(os.sep)
            if len(parts) >= 1 and parts[0].isdigit():
                year = parts[0]
                if year not in by_year:
                    by_year[year] = []
                by_year[year].append(folder)
            else:
                if 'other' not in by_year:
                    by_year['other'] = []
                by_year['other'].append(folder)
        
        # Print organized results
        for year in sorted(by_year.keys()):
            if year != 'other':
                print(f"\n{year}:")
                for folder in sorted(by_year[year]):
                    print(f"  {folder}")
        
        if 'other' in by_year:
            print(f"\nOther:")
            for folder in sorted(by_year['other']):
                print(f"  {folder}")
        
        print(f"\nSUMMARY: {len(empty_folders)} empty folders found")
        print(f"Empty folders represent {len(empty_folders)}/{total_folders} ({100*len(empty_folders)/total_folders:.1f}%) of all folders")
        
    else:
        print("✅ No empty folders found!")
        print("All folders contain files or non-empty subdirectories.")
    
    # Additional analysis for your orca data
    print("\n" + "=" * 80)
    print("ORCA DATA ANALYSIS:")
    print("-" * 40)
    
    years_found = set()
    months_found = set()
    
    for root, dirs, files in os.walk(base_directory):
        path_parts = root.replace(base_directory, '').strip(os.sep).split(os.sep)
        
        if len(path_parts) >= 1 and path_parts[0] and path_parts[0].isdigit():
            years_found.add(int(path_parts[0]))
            
        if len(path_parts) >= 2 and path_parts[1]:
            months_found.add(path_parts[1])
    
    if years_found:
        print(f"Years with data: {min(years_found)} - {max(years_found)} ({len(years_found)} years)")
        print(f"Months found: {sorted(months_found)}")
        
        # Check for missing years
        full_range = set(range(min(years_found), max(years_found) + 1))
        missing_years = full_range - years_found
        if missing_years:
            print(f"Missing years: {sorted(missing_years)}")
    
    print(f"\nTotal sighting files: {total_files}")