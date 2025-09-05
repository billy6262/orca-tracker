import requests
from bs4 import BeautifulSoup
import re
import os
from datetime import datetime
import time
from urllib.parse import urljoin

low_coverage_months = []

def create_folder_structure(base_path, year):
    """Create yearly and monthly folders if they don't exist."""
    months = [
        "January", "February", "March", "April", "May", "June",
        "July", "August", "September", "October", "November", "December"
    ]
    
    # Create year folder
    year_path = os.path.join(base_path, str(year))
    if not os.path.exists(year_path):
        os.makedirs(year_path)
        print(f"Created year folder: {year_path}")
    
    # Create month folders within the year
    for month in months:
        month_path = os.path.join(year_path, month)
        if not os.path.exists(month_path):
            os.makedirs(month_path)
            print(f"Created folder: {month_path}")

def clean_text_for_parsing(text):
    """Clean text by removing HTML artifacts, extra whitespace, and formatting."""
    # Remove HTML entities
    text = re.sub(r'&[a-zA-Z0-9#]+;', ' ', text)
    # Remove extra whitespace, tabs, newlines but preserve line breaks
    text = re.sub(r'[ \t]+', ' ', text)
    # Clean up punctuation spacing
    text = re.sub(r'\s*[,.:;]\s*', ', ', text)
    return text.strip()

def preprocess_single_line_text(text):
    """
    Preprocess text that might be all on one line by adding line breaks
    at logical separation points like date headers and asterisks.
    """
    # If text has very few line breaks but is long, it's likely all on one line
    line_count = text.count('\n')
    text_length = len(text)
    
    print(f"Text analysis: {text_length} chars, {line_count} line breaks")
    
    if text_length > 1000:
        print(f"Preprocessing text for better parsing...")
        
        # First, add line breaks before date patterns like "October 31" or "October 30"
        # This pattern specifically looks for month + day at the start of logical sections
        date_patterns = [
            # Match month + day patterns that are likely headers
            r'(\b(?:january|february|march|april|may|june|july|august|september|october|november|december)\s+\d{1,2}(?:st|nd|rd|th)?(?:\s*,?\s*\d{4})?)',
        ]
        
        for pattern in date_patterns:
            # Add line break before each date pattern (but not at the very start)
            text = re.sub(pattern, r'\n\1', text, flags=re.IGNORECASE)
        
        # Add line breaks before asterisks (common separators)
        text = re.sub(r'\s*\*\s*', '\n*\n', text)
        
        # Add line breaks before common time patterns that start entries
        text = re.sub(r'(\d{1,2}:\d{2}(?:\s*[AP]M)?)', r'\n\1', text)
        
        # Add line breaks before common location/time patterns
        text = re.sub(r'(\d{1,2}:\d{2}\s*-)', r'\n\1', text)
        
        # Clean up multiple consecutive line breaks
        text = re.sub(r'\n\s*\n\s*\n+', '\n\n', text)
        
        # Remove line break at the very beginning if added
        text = text.lstrip('\n')
        
        new_line_count = text.count('\n')
        print(f"After preprocessing: {new_line_count} line breaks")
    
    return text

def extract_date_from_text(text, expected_month=None, expected_year=None):
    """Extract date from plain text format, handling dates with and without years."""
    # Month abbreviations and full names mapping
    month_mapping = {
        'Jan': 'January', 'Feb': 'February', 'Mar': 'March',
        'Apr': 'April', 'May': 'May', 'Jun': 'June',
        'Jul': 'July', 'Aug': 'August', 'Sep': 'September',
        'Oct': 'October', 'Nov': 'November', 'Dec': 'December',
        'January': 'January', 'February': 'February', 'March': 'March',
        'April': 'April', 'May': 'May', 'June': 'June',
        'July': 'July', 'August': 'August', 'September': 'September',
        'October': 'October', 'November': 'November', 'December': 'December'
    }
    
    # Patterns for date extraction - with and without years
    patterns = [
        # With year: "June 30, 2004", "Tue, June 30, 2020"
        r'(?:\w+,?\s+)?(\w+)\s+(\d{1,2})(?:st|nd|rd|th)?,?\s*(\d{4})',
        # Without year: "Tue, June 30", "June 30", "October 31"
        r'(?:\w+,?\s+)?(\w+)\s+(\d{1,2})(?:st|nd|rd|th)?(?:\s*-.*)?$',
        # Day first with year: "30 June 2004"
        r'(\d{1,2})\s+(\w+)\s+(\d{4})',
        # Day first without year: "30 June"
        r'(\d{1,2})\s+(\w+)(?:\s*-.*)?$',
    ]
    
    for pattern in patterns:
        match = re.search(pattern, text, re.IGNORECASE)
        if match:
            groups = match.groups()
            
            # Handle different formats
            if len(groups) >= 3 and groups[2] and groups[2].isdigit():
                # Has year
                if groups[0].isdigit():
                    # Format: day, month, year
                    day_str, month_str, year_str = groups[:3]
                else:
                    # Format: month, day, year
                    month_str, day_str, year_str = groups[:3]
            else:
                # No year - use expected year
                if groups[0].isdigit():
                    # Format: day, month
                    day_str, month_str = groups[:2]
                else:
                    # Format: month, day
                    month_str, day_str = groups[:2]
                year_str = str(expected_year) if expected_year else None
            
            # Normalize month name
            month_str = month_mapping.get(month_str, month_str)
            
            # Validate month
            if month_str not in month_mapping.values():
                continue
            
            # Check if month matches expected month
            if expected_month and month_str != expected_month:
                continue
            
            # Extract day
            try:
                day = int(re.sub(r'[^\d]', '', day_str))
                if not (1 <= day <= 31):
                    continue
            except ValueError:
                continue
            
            # Extract year
            if year_str:
                try:
                    year = int(year_str)
                    if not (2001 <= year <= 2030):
                        year = expected_year if expected_year else datetime.now().year
                except ValueError:
                    year = expected_year if expected_year else datetime.now().year
            else:
                year = expected_year if expected_year else datetime.now().year
            
            # Check if year matches expected year
            if expected_year and year != expected_year:
                continue
            
            return month_str, day, year
    
    return None, None, None

def is_date_line(line, expected_month=None, expected_year=None):
    """Check if a line contains a date header (with or without year)."""
    line = line.strip()
    
    # Skip very short or very long lines
    if len(line) < 5 or len(line) > 100:
        return False
    
    # Must contain month and day patterns
    month_pattern = r'\b(january|february|march|april|may|june|july|august|september|october|november|december|jan|feb|mar|apr|may|jun|jul|aug|sep|oct|nov|dec)\b'
    day_pattern = r'\b([1-9]|[12][0-9]|3[01])(?:st|nd|rd|th)?\b'
    year_pattern = r'\b(19\d{2}|20[0-3]\d)\b'
    weekday_pattern = r'\b(monday|tuesday|wednesday|thursday|friday|saturday|sunday|mon|tue|wed|thu|fri|sat|sun)\b'
    
    has_month = bool(re.search(month_pattern, line, re.IGNORECASE))
    has_day = bool(re.search(day_pattern, line, re.IGNORECASE))
    has_year = bool(re.search(year_pattern, line, re.IGNORECASE))
    has_weekday = bool(re.search(weekday_pattern, line, re.IGNORECASE))
    
    # Must have month and day - year is optional
    if not (has_month and has_day):
        return False
    
    # If expected_month is provided, check if the text contains that month
    if expected_month:
        expected_month_pattern = rf'\b{expected_month.lower()}\b|\b{expected_month[:3].lower()}\b'
        if not re.search(expected_month_pattern, line, re.IGNORECASE):
            return False
    
    # For years with explicit year, check if the year matches
    if has_year and expected_year:
        year_match = re.search(year_pattern, line, re.IGNORECASE)
        if year_match:
            found_year = int(year_match.group(1))
            if found_year != expected_year:
                return False
    elif has_year:
        # If line has a year but no expected year, consider it a date line
        return True
    
    return True

def determine_year_from_url(url):
    """Extract year from URL or filename."""
    year_match = re.search(r'(\d{4})', url)
    if year_match:
        year = int(year_match.group(1))
        if 2001 <= year <= 2030:
            return year
    return datetime.now().year

def determine_month_from_url(url):
    """Extract month from URL."""
    month_mapping = {
        'january': 'January', 'february': 'February', 'march': 'March',
        'april': 'April', 'may': 'May', 'june': 'June',
        'july': 'July', 'august': 'August', 'september': 'September',
        'october': 'October', 'november': 'November', 'december': 'December',
        'jan': 'January', 'feb': 'February', 'mar': 'March',
        'apr': 'April', 'may': 'May', 'jun': 'June',
        'jul': 'July', 'aug': 'August', 'sep': 'September',
        'oct': 'October', 'nov': 'November', 'dec': 'December'
    }
    
    for month_key, month_name in month_mapping.items():
        if month_key in url.lower():
            return month_name
    return None

def analyze_month_coverage(sightings_by_date):
    """Analyze month coverage and return months with fewer than 15 dates."""
    global low_coverage_months
    
    # Group dates by year-month
    dates_by_month = {}
    
    for date_key in sightings_by_date.keys():
        year, month, day = date_key.split('_')
        month_key = f"{year}_{month}"
        
        if month_key not in dates_by_month:
            dates_by_month[month_key] = set()
        
        dates_by_month[month_key].add(int(day))
    
    # Find months with fewer than 15 dates
    for month_key, days in dates_by_month.items():
        if len(days) < 15:
            year, month = month_key.split('_')
            month_info = f"{month} {year} ({len(days)} dates)"
            if month_info not in low_coverage_months:  # Avoid duplicates
                low_coverage_months.append(month_info)
    
    return low_coverage_months

def parse_plain_text_content(text_content, expected_year, expected_month=None):
    """Parse plain text content and extract sighting data organized by date."""
    # Preprocess text to handle single-line data
    text_content = preprocess_single_line_text(text_content)
    
    lines = text_content.split('\n')
    
    print(f"Processing {len(lines)} lines of text")
    print(f"Looking for dates in {expected_month} {expected_year}")
    
    sightings_by_date = {}
    current_date_key = None
    date_headers_found = 0
    rejected_headers = 0
    dates_with_entry_counts = {}
    processed_reports = set()  # Track processed reports to avoid duplicates
    
    current_entry = []
    
    for line_num, line in enumerate(lines):
        line = line.strip()
        
        if not line:
            # Empty line - add to current entry if we have content
            if current_entry and current_date_key:
                current_entry.append("")
            continue
        
        # Check if this line is a date header
        if is_date_line(line, expected_month, expected_year):
            month, day, year = extract_date_from_text(line, expected_month, expected_year)
            
            if month and day and year:
                # Save previous entry if exists
                if current_date_key and current_entry:
                    entry_text = '\n'.join(current_entry).strip()
                    if len(entry_text) > 20:
                        # Create a hash of the content to check for duplicates
                        content_hash = hash(entry_text.lower().replace(' ', '').replace('\n', ''))
                        
                        if content_hash not in processed_reports:
                            sightings_by_date[current_date_key].append(entry_text)
                            processed_reports.add(content_hash)
                            print(f"Added unique report to {current_date_key}")
                        else:
                            print(f"Skipped duplicate report for {current_date_key}")
                
                # Start new date section (or continue existing one)
                new_date_key = f"{year}_{month}_{day:02d}"
                
                # Initialize date if first time seeing it
                if new_date_key not in sightings_by_date:
                    sightings_by_date[new_date_key] = []
                    dates_with_entry_counts[new_date_key] = 0
                
                # Track headers for this date
                if new_date_key != current_date_key:
                    dates_with_entry_counts[new_date_key] += 1
                    print(f"Found date header #{date_headers_found + 1}: {month} {day}, {year}")
                    date_headers_found += 1
                else:
                    dates_with_entry_counts[new_date_key] += 1
                    print(f"Found additional header for {month} {day}, {year}")
                
                current_date_key = new_date_key
                current_entry = []
                continue
        
        # Add line to current entry if we have a current date
        if current_date_key:
            current_entry.append(line)
    
    # Don't forget the last entry
    if current_date_key and current_entry:
        entry_text = '\n'.join(current_entry).strip()
        if len(entry_text) > 20:
            content_hash = hash(entry_text.lower().replace(' ', '').replace('\n', ''))
            if content_hash not in processed_reports:
                sightings_by_date[current_date_key].append(entry_text)
                processed_reports.add(content_hash)
                print(f"Added final unique report to {current_date_key}")
    
    print(f"Total date headers found: {date_headers_found}")
    print(f"Total unique reports processed: {len(processed_reports)}")
    
    # Find months with fewer than 15 dates
    analyze_month_coverage(sightings_by_date)
    
    return sightings_by_date

def parse_sighting_data(html_content, default_year, expected_month=None, target_line=0):
    """Parse HTML content and extract sighting data organized by date."""
    soup = BeautifulSoup(html_content, 'html.parser')
    
    # Try multiple approaches to extract the content
    plain_text = None
    
    # Method 1: Look for the specific structure in the HTML
    sqs_html_content = soup.select('div.sqs-html-content')
    if sqs_html_content:
        print("Found sqs-html-content div, extracting text...")
        plain_text = sqs_html_content[0].get_text(separator='\n', strip=True)
    
    # Method 2: Look for paragraph with white-space:pre-wrap style
    if not plain_text:
        pre_wrap_paragraphs = soup.select('p[style*="white-space:pre-wrap"]')
        if pre_wrap_paragraphs:
            print("Found pre-wrap paragraph, extracting text...")
            plain_text = pre_wrap_paragraphs[0].get_text(separator='\n', strip=True)
    
    # Method 3: Try the original selectors
    if not plain_text:
        content_selectors = [
            'div.sqs-block-content',
            'div.entry-content', 
            'main',
            'article',
            '.content',
            'body'
        ]
        
        for selector in content_selectors:
            elements = soup.select(selector)
            if elements:
                print(f"Found content using selector: {selector}")
                plain_text = elements[0].get_text(separator='\n', strip=True)
                break
    
    # Method 4: Fallback to body text
    if not plain_text:
        print("Falling back to body text extraction...")
        plain_text = soup.get_text(separator='\n', strip=True)
    
    if plain_text and len(plain_text) > 100:
        print(f"Found plain text content ({len(plain_text)} chars), parsing as text format")
        print(f"Text preview: '{plain_text[:200]}...'")
        return parse_plain_text_content(plain_text, default_year, expected_month)
    else:
        print(f"No substantial plain text found (got {len(plain_text) if plain_text else 0} chars)")
        if plain_text:
            print(f"Content preview: '{plain_text}'")
    
    # If no plain text found, fall back to original HTML parsing
    print("No plain text found, falling back to HTML parsing")
    
    # Get all <strong> elements specifically for date headers
    strong_elements = soup.find_all('strong')
    all_elements = soup.find_all(['p', 'div', 'span', 'h1', 'h2', 'h3', 'h4', 'h5', 'h6', 'strong', 'em', 'b', 'i'])
    
    print(f"Found {len(strong_elements)} <strong> elements (potential date headers)")
    
    sightings_by_date = {}
    date_headers_found = 0
    rejected_headers = 0
    dates_with_entry_counts = {}
    
    # Find all valid date headers in <strong> elements
    date_headers = []
    for strong_elem in strong_elements:
        text = strong_elem.get_text().strip()
        
        if is_date_line(text, expected_month, default_year):
            month, day, year = extract_date_from_text(text, expected_month, default_year)
            
            if month and day and year:
                if expected_month and month != expected_month:
                    rejected_headers += 1
                    continue
                
                if year != default_year:
                    rejected_headers += 1
                    continue
                
                date_key = f"{year}_{month}_{day:02d}"
                
                # Track multiple headers for same date
                if date_key not in dates_with_entry_counts:
                    dates_with_entry_counts[date_key] = 0
                dates_with_entry_counts[date_key] += 1
                
                date_headers.append({
                    'element': strong_elem,
                    'text': text,
                    'month': month,
                    'day': day,
                    'year': year,
                    'date_key': date_key
                })
                date_headers_found += 1
                print(f"Found date header #{date_headers_found}: {month} {day}, {year} (Header #{dates_with_entry_counts[date_key]} for this date)")
    
    # Process content sequentially
    current_header = None
    
    for element in all_elements:
        text = element.get_text().strip()
        
        if not text:
            continue
        
        # Check if this element is a date header
        is_current_header = False
        for header in date_headers:
            if element == header['element'] or element.find('strong') == header['element']:
                current_header = header
                current_date_key = header['date_key']
                if current_date_key not in sightings_by_date:
                    sightings_by_date[current_date_key] = []
                is_current_header = True
                break
        
        # Add content to current date
        if not is_current_header and current_header:
            cleaned_text = text.strip()
            if (len(cleaned_text) > 15 and 
                not re.match(r'^[*\-=_\s]+$', cleaned_text) and
                not re.match(r'^\s*\d+\s*$', cleaned_text) and
                not is_date_line(cleaned_text, expected_month, default_year)):
                sightings_by_date[current_header['date_key']].append(cleaned_text)
    
    print(f"Total date headers found: {date_headers_found}")
    print(f"Total headers rejected: {rejected_headers}")
    
    # Find months with fewer than 15 dates
    analyze_month_coverage(sightings_by_date)
    
    return sightings_by_date

def save_sightings_to_files(sightings_data, base_path):
    """Save sighting data to individual text files organized by year and month."""
    for date_key, sighting_texts in sightings_data.items():
        if not sighting_texts:  # Skip empty dates
            continue
            
        year, month, day = date_key.split('_')
        year = int(year)
        day = int(day)
        
        # Create year and month folder path
        year_folder = os.path.join(base_path, str(year))
        month_folder = os.path.join(year_folder, month)
        
        if not os.path.exists(month_folder):
            os.makedirs(month_folder)
        
        # Create filename with year
        filename = f"{year}_{month}_{day:02d}.txt"
        filepath = os.path.join(month_folder, filename)
        
        # Write sighting data to file
        with open(filepath, 'w', encoding='utf-8') as f:
            f.write(f"Orca Sightings for {month} {day}, {year}\n")
            f.write("=" * 60 + "\n\n")
            
            for i, sighting in enumerate(sighting_texts, 1):
                f.write(f"Entry {i}:\n")
                f.write(sighting + "\n\n")
        
        print(f"Saved {len(sighting_texts)} sightings to {filepath}")

def process_local_html_file(file_path):
    """Process a local HTML file for testing."""
    try:
        print(f"Processing local file: {file_path}")
        
        with open(file_path, 'r', encoding='utf-8') as f:
            html_content = f.read()
        
        # Determine year and month from filename
        filename = os.path.basename(file_path)
        year_match = re.search(r'(\d{4})', filename)
        year = int(year_match.group(1)) if year_match else datetime.now().year
        
        month_match = re.search(r'(january|february|march|april|may|june|july|august|september|october|november|december)', filename.lower())
        month = month_match.group(1).capitalize() if month_match else None
        
        print(f"Detected year: {year}")
        print(f"Detected month: {month}")
        
        # Parse the sighting data
        sightings_data = parse_sighting_data(html_content, year, month)
        
        if not sightings_data:
            print("No sighting data found")
            return
        
        print(f"Found sightings for {len(sightings_data)} dates")
        
        # Get the current script directory
        script_dir = os.path.dirname(os.path.abspath(__file__))
        
        # Create folder structure for the specific year
        create_folder_structure(script_dir, year)
        
        # Save sightings to files
        save_sightings_to_files(sightings_data, script_dir)
        
        print("Successfully processed and saved all sighting data!")
        
    except Exception as e:
        print(f"Error processing file: {e}")

def fetch_orca_sightings(url, target_line=0):
    """Main function to fetch and process orca sightings."""
    try:
        print(f"Fetching data from: {url}")
        
        # Determine year and month from URL
        year = determine_year_from_url(url)
        month = determine_month_from_url(url)
        print(f"Detected year: {year}")
        print(f"Detected month: {month}")
        
        # Add headers to mimic a browser request
        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36',
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
            'Accept-Language': 'en-US,en;q=0.5',
            'Accept-Encoding': 'gzip, deflate',
            'Connection': 'keep-alive',
            'Upgrade-Insecure-Requests': '1',
        }
        
        response = requests.get(url, headers=headers, timeout=30)
        response.raise_for_status()
        
        print(f"Successfully fetched HTML content ({len(response.content)} bytes)")
        
        # Parse the sighting data with month filtering
        sightings_data = parse_sighting_data(response.text, year, month, target_line)
        
        if not sightings_data:
            print("No sighting data found")
            return
        
        print(f"Found sightings for {len(sightings_data)} dates")
        
        # Get the current script directory
        script_dir = os.path.dirname(os.path.abspath(__file__))
        
        # Create folder structure for the specific year
        create_folder_structure(script_dir, year)
        
        # Save sightings to files
        save_sightings_to_files(sightings_data, script_dir)
        
        print("Successfully processed and saved all sighting data!")
        
    except requests.RequestException as e:
        print(f"Error fetching URL: {e}")
    except Exception as e:
        print(f"Error processing data: {e}")

def fetch_multiple_months(year=2025):
    """Fetch data for multiple months of a specific year."""
    base_url = "https://indigo-ukulele-jm29.squarespace.com"
    months = [
        "january", "february", "march", "april",
        "may", "june", "july", "august",
        "september", "october", "november", "december"
    ]
    
    for month in months:
        url = f"{base_url}/{month}-{year}"
        print(f"\n--- Processing {month} {year} ---")
        
        try:
            fetch_orca_sightings(url)
            # Add delay between requests to be respectful
            time.sleep(2)
        except Exception as e:
            print(f"Error processing {month} {year}: {e}")
            continue

def fetch_historical_data(start_year=2001, end_year=2025):
    """Fetch historical data from start_year to end_year."""
    global low_coverage_months
    
    print(f"Fetching historical data from {start_year} to {end_year}")
    low_coverage_months = []  # Reset at start

    for year in range(start_year, end_year + 1):
        print(f"\n=== Processing Year {year} ===")
        
        # Only process from April 2001 onwards
        if year == 2001:
            # For 2001, start from April
            months = ["april", "may", "june", "july", "august", "september", "october", "november", "december"]
        else:
            months = [
                "january", "february", "march", "april",
                "may", "june", "july", "august", 
                "september", "october", "november", "december"
            ]
        
        for month in months:
            url = f"https://indigo-ukulele-jm29.squarespace.com/{month}-{year}"
            print(f"\n--- Processing {month} {year} ---")
            
            try:
                fetch_orca_sightings(url)
                time.sleep(2)  # Respectful delay
            except Exception as e:
                print(f"Error processing {month} {year}: {e}")
                continue
        
        # Add longer delay between years
        time.sleep(5)
    
    # Print final summary
    if low_coverage_months:
        print(f"\n=== FINAL SUMMARY: Months with fewer than 15 dates ===")
        for month_info in sorted(set(low_coverage_months)):
            print(f"  - {month_info}")
    else:
        print(f"\n=== FINAL SUMMARY: All months have 15 or more dates ===")

if __name__ == "__main__":
    # Example usage options:
    
    # 1. Process the local HTML file for testing
    #local_file = r"c:\Users\andre\OneDrive\Desktop\Web Dev\orca tracker\Raw_text_reports\October 2022 — Orca Network Archives.htm"
    #process_local_html_file(local_file)
    
    # 2. Fetch a single month for testing
    url = "https://www.orcanetwork.org/recent-sightings"
    fetch_orca_sightings(url, target_line=0)
    
    # 3. Fetch all months for a specific year
    # fetch_multiple_months(2022)
    
    # 4. Fetch historical data
    #fetch_historical_data(2001, 2025)
    
    # 5. Fetch specific year range for testing
    # fetch_historical_data(2020, 2021)