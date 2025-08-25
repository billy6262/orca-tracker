import os
import logging
import json  # Move this to the top level imports
from typing import List, Dict, Any
from dateutil import parser as dtparser
from django.db import transaction
import openai
from .models import RawReport, OrcaSighting
import chardet  # Add this import for encoding detection
import time
import random

logger = logging.getLogger(__name__)

MODEL_NAME = os.getenv("OPENAI_MODEL", "gpt-5")

# Global client variable - will be initialized when needed
_client = None

def get_openai_api_key():
    """Get OpenAI API key from secrets folder or environment variables with encoding detection."""
    # First try to read from secrets folder
    # Check if running in Docker (secrets mounted at /secrets)
    if os.path.exists('/secrets/openai_api_key.txt'):
        api_key_path = '/secrets/openai_api_key.txt'
    else:
        # Local development - secrets folder in parent directory
        base_dir = os.path.dirname(os.path.dirname(os.path.dirname(__file__)))
        api_key_path = os.path.join(base_dir, 'secrets', 'openai_api_key.txt')
    
    if os.path.exists(api_key_path):
        try:
            # Use the same encoding detection function for the API key file
            api_key_content = read_file_with_encoding_detection(api_key_path)
            return api_key_content.strip()
        except Exception as e:
            logger.warning(f"Failed to read API key file with encoding detection: {e}")
            # Fallback to simple UTF-8 read
            try:
                with open(api_key_path, 'r', encoding='utf-8') as f:
                    return f.read().strip()
            except Exception as e2:
                logger.error(f"Failed to read API key file: {e2}")
                raise ValueError(f"Could not read OpenAI API key from {api_key_path}: {e2}")
    
    # Fallback to environment variable
    api_key = os.getenv('OPENAI_API_KEY')
    if api_key:
        return api_key.strip()
    
    raise ValueError("OpenAI API key not found in secrets folder or environment variables")

def get_openai_client():
    """Get or create OpenAI client instance."""
    global _client
    if _client is None:
        _client = openai.OpenAI(api_key=get_openai_api_key())
    return _client

def read_file_with_encoding_detection(file_path: str) -> str:
    """
    Read a file with automatic encoding detection.
    Tries multiple encodings to handle various file formats.
    """
    # List of encodings to try in order
    encodings_to_try = [
        'utf-8',
        'utf-8-sig',  # UTF-8 with BOM
        'utf-16',     # UTF-16 with BOM
        'utf-16le',   # UTF-16 Little Endian
        'utf-16be',   # UTF-16 Big Endian
        'windows-1252',  # Windows encoding
        'iso-8859-1',    # Latin-1
        'cp1252',        # Windows CP1252
    ]
    
    # First, try to detect encoding using chardet
    try:
        with open(file_path, 'rb') as f:
            raw_data = f.read()
        
        # Detect encoding
        detected = chardet.detect(raw_data)
        detected_encoding = detected.get('encoding')
        confidence = detected.get('confidence', 0)
        
        logger.debug(f"Detected encoding for {file_path}: {detected_encoding} (confidence: {confidence:.2f})")
        
        # If confidence is high, try the detected encoding first
        if detected_encoding and confidence > 0.7:
            try:
                return raw_data.decode(detected_encoding)
            except (UnicodeDecodeError, LookupError):
                logger.warning(f"Failed to decode with detected encoding {detected_encoding}")
        
    except Exception as e:
        logger.warning(f"Error detecting encoding for {file_path}: {e}")
    
    # Try each encoding in our list
    for encoding in encodings_to_try:
        try:
            with open(file_path, 'r', encoding=encoding) as f:
                content = f.read()
            logger.debug(f"Successfully read {file_path} with encoding: {encoding}")
            return content
        except (UnicodeDecodeError, UnicodeError):
            continue
        except Exception as e:
            logger.warning(f"Error reading {file_path} with encoding {encoding}: {e}")
            continue
    
    # If all else fails, read as binary and decode with errors='replace'
    try:
        with open(file_path, 'rb') as f:
            raw_data = f.read()
        content = raw_data.decode('utf-8', errors='replace')
        logger.warning(f"Read {file_path} with error replacement - some characters may be corrupted")
        return content
    except Exception as e:
        logger.error(f"Failed to read {file_path} with any encoding: {e}")
        raise

JSON_SCHEMA = {
    "name": "orca_sightings_schema",
    "schema": {
        "type": "object",
        "properties": {
            "sightings": {
                "type": "array",
                "items": {
                    "type": "object",
                    "required": ["time", "zone", "direction", "count"],
                    "properties": {
                        "time": {
                            "type": "string",
                            "description": "ISO 8601 datetime (UTC if not specified)."
                        },
                        "zone": {
                            "type": "string",
                            "description": "Geographic zone / area name extracted from report."
                        },
                        "direction": {
                            "type": "string",
                            "description": "Movement direction (e.g., N, S, NW, inbound, unknown)."
                        },
                        "count": {
                            "type": "integer",
                            "description": "Estimated number of orcas; use best single integer. If a range, pick the midpoint rounded."
                        }
                    }
                }
            }
        },
        "required": ["sightings"],
        "additionalProperties": False
    }
}

PROMPT_TEMPLATE = """You are an information extraction system for whale sighting reports.

Extract every distinct Orca sighting from the email body.

Rules:
- If no Orca mentioned, return an empty sightings array.
- Normalize direction to a short cardinal/ordinal if possible (N,S,E,W,NE,NW,SE,SW) else 'unknown'.
- If time not explicitly given, omit the sighting (do not guess).
- Convert all times to ISO 8601; if date missing assume today's date in reporter's apparent timezone, else leave.
- Count: if a range like 6-8, take midpoint (7). If vague like "several", use a reasonable guess: several=5, few=3, couple=2, many=10, pod=6. If calves mentioned add them.

Zone Reference:
1 Strait of Juan de Fuca West - Cape Flattery approaches, Tatoosh Island waters, Waatch Point, Makah Bay offshore, Shi Shi offshore, Swiftsure Bank US side edge
2 Strait of Juan de Fuca Central - Clallam Bay, Slip Point, Pillar Point shoals, Freshwater Bay, Angeles Point, Twin Rivers offshore
3 Strait of Juan de Fuca East - Port Angeles outer harbor, Dungeness Spit offshore, Protection Island waters, Discovery Bay mouth, Partridge Bank
4 San Juan Islands Northwest - Stuart Island, Turn Point, Johns Pass, Waldron Island, Speiden Channel, Henry Island, Mosquito Pass, Roche Harbor
5 San Juan Islands Northeast & Bellingham Outer - Patos, Sucia, Matia, Clark Island, Alden Bank edge, Parker Reef, Lummi Island north/west, Bellingham Bay outer, Portage/Legoe Bay
6 San Juan Islands Southwest - Lime Kiln whale trail, Smallpox Bay, Deadman Bay, Eagle Point, South Beach, Cattle Pass rips, Salmon Bank
7 San Juan Islands Southeast & Central Rosario - San Juan Channel, Wasp Islands, West Sound Orcas, East Sound mouth, Lopez Pass, Upright Channel, Thatcher Pass
8 Rosario South & Fidalgo Deception - Cypress Head, Strawberry Island, Guemes Channel, Burrows Bay, Allan Island, Deception Pass both mouths, Skagit Bay outer
9 Admiralty Inlet - Point Wilson rip, Port Townsend Bay outer, Marrowstone/Indian Island, Mutiny Bay, Double Bluff, Smith Island
10 Saratoga Passage & Port Susan - Langley, Baby Island, Camano east shore, Hat/Johns Islands, Kayak Point, Port Susan, Camano Head
11 Hood Canal entire - Hood Canal Bridge, Bangor area waters, Dabob Bay, Quilcene Bay, Toandos Peninsula, Brinnon/Dosewallips, Hoodsport/Great Bend
12 Central Sound North - Possession Bar, Edmonds ferry lanes, Kingston approaches, Jefferson Head, Apple Tree Cove, Port Madison
13 Central Sound South - Shilshole Bay, Elliott Bay outer, West Point, Bainbridge east shore, Blakely Rock, Rich Passage, Blake Island
14 Tacoma Narrows & Dalco - Colvos Passage, Dalco Passage, Point Defiance, Tacoma Narrows both bridges, Gig Harbor entrance
15 South Sound West Basins - Carr Inlet, Case Inlet, North Bay, Pickering Passage, Totten Inlet, Eld Inlet, Jarrell Cove
16 South Sound East Basins - Commencement Bay, Colvos south mouth, Dana Passage, Budd Inlet, Henderson Inlet, Nisqually Reach, Devils Head/Anderson Ketron

Return only zones 1-16 as above. If a location is not clearly in one of these zones, pick the nearest zone.
Use zone numbers rather than names.
Return ONLY JSON compliant with the provided schema.
Email body:
---
{body}
---"""

def _coerce_int(value):
    try:
        return int(value)
    except:
        return None

def _calc_derived_fields(dt):
    return dt.month, dt.isoweekday(), dt.hour

def _create_sighting(raw: RawReport, data: Dict[str, Any]):
    """Create OrcaSighting with derived placeholder stats (0 for now)."""
    # Check if data is a string instead of a dict
    if isinstance(data, str):
        logger.warning(f"Received string instead of dict for sighting data: {data[:100]}... - skipping")
        return
    
    # Check if data is a dict
    if not isinstance(data, dict):
        logger.warning(f"Received unexpected data type {type(data)} for sighting data: {data} - skipping")
        return
    
    try:
        dt = dtparser.parse(data["time"])
    except KeyError:
        logger.warning(f"Missing 'time' field in sighting data for report {raw.messageId}")
        return
    except Exception:
        logger.warning(f"Could not parse time '{data.get('time')}' for report {raw.messageId}")
        return
    
    month, dow, hour = _calc_derived_fields(dt)
    count = _coerce_int(data.get("count"))
    if count is None or count < 0:
        logger.warning(f"Invalid count '{data.get('count')}' for report {raw.messageId}")
        return
    
    try:
        OrcaSighting.objects.create(
            raw_report=raw,
            time=dt,
            zone=data.get("zone", "").strip()[:100],
            direction=data.get("direction", "").strip()[:50],
            count=count,
            month=month,
            dayOfWeek=dow,
            hour=hour,
            reportsIn5h=0,
            reportsIn24h=0,
            reportsInAdjacentZonesIn5h=0,
            reportsInAdjacentPlusZonesIn5h=0
        )
    except Exception as e:
        logger.error(f"Failed to create OrcaSighting for report {raw.messageId}: {e}")

def _extract_sightings(body: str) -> List[Dict[str, Any]]:
    if not body.strip():
        return []
    
    # Retry configuration
    max_retries = 3
    base_delay = 1  # seconds
    
    for attempt in range(max_retries):
        try:
            client = get_openai_client()
            response = client.chat.completions.create(
                model=MODEL_NAME,
                messages=[{"role": "user", "content": PROMPT_TEMPLATE.format(body=body)}],
                response_format={
                    "type": "json_schema",
                    "json_schema": JSON_SCHEMA
                },
                service_tier="flex",
                #timeout=30  # Add timeout
            )
            
            # json is now imported at module level
            parsed = json.loads(response.choices[0].message.content)
            sightings = parsed.get("sightings", [])
            
            # Validate that sightings is a list and contains dicts
            if not isinstance(sightings, list):
                logger.error(f"Expected sightings to be a list, got {type(sightings)}: {sightings}")
                return []
            
            # Filter out non-dict items and log them
            valid_sightings = []
            for i, sight in enumerate(sightings):
                if isinstance(sight, dict):
                    # Validate required fields
                    if all(key in sight for key in ["time", "zone", "direction", "count"]):
                        valid_sightings.append(sight)
                    else:
                        missing_keys = [key for key in ["time", "zone", "direction", "count"] if key not in sight]
                        logger.warning(f"Sighting {i} missing required keys {missing_keys}: {sight}")
                else:
                    logger.warning(f"Sighting {i} is not a dict, got {type(sight)}: {sight}")
            
            logger.debug(f"Extracted {len(valid_sightings)} valid sightings out of {len(sightings)} total")
            return valid_sightings
            
        except json.JSONDecodeError as e:
            logger.error(f"Failed to parse JSON response: {e}")
            logger.error(f"Raw response: {response.choices[0].message.content if 'response' in locals() else 'No response'}")
            return []
        except openai.APITimeoutError as e:
            logger.warning(f"OpenAI API timeout (attempt {attempt + 1}/{max_retries}): {e}")
            if attempt < max_retries - 1:
                delay = base_delay * (2 ** attempt) + random.uniform(0, 1)
                logger.info(f"Retrying in {delay:.2f} seconds...")
                time.sleep(delay)
                continue
            return []
        except openai.RateLimitError as e:
            logger.warning(f"OpenAI rate limit hit (attempt {attempt + 1}/{max_retries}): {e}")
            if attempt < max_retries - 1:
                delay = base_delay * (2 ** attempt) + random.uniform(5, 10)  # Longer delay for rate limits
                logger.info(f"Retrying in {delay:.2f} seconds...")
                time.sleep(delay)
                continue
            return []
        except openai.APIError as e:
            if e.status_code == 500:
                logger.warning(f"OpenAI server error (attempt {attempt + 1}/{max_retries}): {e}")
                if attempt < max_retries - 1:
                    delay = base_delay * (2 ** attempt) + random.uniform(0, 1)
                    logger.info(f"Retrying in {delay:.2f} seconds...")
                    time.sleep(delay)
                    continue
            logger.error(f"OpenAI API error: {e}")
            return []
        except Exception as e:
            logger.error(f"Failed to extract sightings: {e}")
            return []
    
    logger.error(f"Failed to extract sightings after {max_retries} attempts")
    return []

@transaction.atomic
def process_unprocessed_reports(limit: int = 25):
    reports = RawReport.objects.select_for_update(skip_locked=True).filter(processed=False)[:limit]
    for report in reports:
        try:
            sightings = _extract_sightings(report.body)
            created = 0
            for sight in sightings:
                _create_sighting(report, sight)
                created += 1
            report.processed = True
            report.save(update_fields=["processed"])
            logger.info(f"Report {report.messageId}: created {created} sightings.")
        except Exception as e:
            logger.exception(f"Error processing report {report.messageId}: {e}")

def process_txt_files_from_nested_folders(base_folder_path: str, move_processed: bool = True, year_filter: List[int] = None, month_filter: List[str] = None):
    """
    Process all .txt files from the nested year/month folder structure created by txt_fetcher.py.
    Skips files that are in folders named "processed" to avoid reprocessing already handled reports.
    
    Args:
        base_folder_path: Path to base folder containing year folders (e.g., Raw_text_reports)
        move_processed: If True, move processed files to 'processed' subfolder within each month
        year_filter: Optional list of years to process (e.g., [2022, 2023])
        month_filter: Optional list of months to process (e.g., ['June', 'July'])
    """
    if not os.path.exists(base_folder_path):
        logger.error(f"Base folder does not exist: {base_folder_path}")
        return
    
    total_files_processed = 0
    total_sightings_created = 0
    encoding_issues = 0
    
    # Get all year folders
    year_folders = [f for f in os.listdir(base_folder_path) 
                   if os.path.isdir(os.path.join(base_folder_path, f)) and f.isdigit()]
    
    # Filter years if specified
    if year_filter:
        year_folders = [y for y in year_folders if int(y) in year_filter]
    
    if not year_folders:
        logger.info(f"No year folders found in {base_folder_path}")
        return
    
    logger.info(f"Processing years: {sorted(year_folders)}")
    
    for year_folder in sorted(year_folders):
        year_path = os.path.join(base_folder_path, year_folder)
        
        # Get all month folders within this year (excluding "processed" folders)
        all_folders = [f for f in os.listdir(year_path) 
                      if os.path.isdir(os.path.join(year_path, f))]
        processed_folders = [f for f in all_folders if f.lower() == "processed"]
        month_folders = [f for f in all_folders if f.lower() != "processed"]
        
        if processed_folders:
            logger.info(f"Skipping {len(processed_folders)} processed folder(s) in {year_folder}: {processed_folders}")
        
        # Filter months if specified
        if month_filter:
            month_folders = [m for m in month_folders if m in month_filter]
        
        if not month_folders:
            logger.info(f"No month folders found in {year_path}")
            continue
        
        logger.info(f"Processing {year_folder}: {len(month_folders)} months")
        
        for month_folder in sorted(month_folders):
            month_path = os.path.join(year_path, month_folder)
            
            # Skip processing if this is a "processed" folder
            if month_folder.lower() == "processed":
                logger.debug(f"Skipping processed folder: {month_path}")
                continue
            
            # Get all .txt files in this month folder (excluding files in "processed" subfolder)
            all_files = []
            for item in os.listdir(month_path):
                item_path = os.path.join(month_path, item)
                if os.path.isfile(item_path) and item.lower().endswith('.txt'):
                    all_files.append(item)
                elif os.path.isdir(item_path) and item.lower() == "processed":
                    # Skip files in processed subfolder
                    logger.debug(f"Skipping files in processed subfolder: {item_path}")
            
            txt_files = all_files
            
            if not txt_files:
                logger.debug(f"No .txt files found in {month_path}")
                continue
            
            logger.info(f"Processing {year_folder}/{month_folder}: {len(txt_files)} files")
            
            # Create processed subfolder if needed
            if move_processed:
                processed_folder = os.path.join(month_path, "processed")
                if not os.path.exists(processed_folder):
                    os.makedirs(processed_folder)
            
            # Process each txt file
            for filename in txt_files:
                file_path = os.path.join(month_path, filename)
                
                try:
                    # Read file content with encoding detection
                    try:
                        content = read_file_with_encoding_detection(file_path)
                    except Exception as e:
                        logger.error(f"Failed to read {year_folder}/{month_folder}/{filename}: {e}")
                        encoding_issues += 1
                        continue
                    
                    # Extract date info from filename (format: YYYY_Month_DD.txt)
                    base_name = os.path.splitext(filename)[0]
                    
                    # Create unique messageId including the full path info
                    message_id = f"txt_file_{year_folder}_{month_folder}_{base_name}"
                    
                    # Check if already processed
                    if RawReport.objects.filter(messageId=message_id).exists():
                        logger.debug(f"File {year_folder}/{month_folder}/{filename} already processed, skipping")
                        continue
                    
                    # Create RawReport entry
                    with transaction.atomic():
                        raw_report = RawReport.objects.create(
                            messageId=message_id,
                            subject=f"Orca Network Archive: {year_folder} {month_folder} - {filename}",
                            sender="orca_network_archive",
                            body=content,
                            processed=False
                        )
                        
                        # Extract sightings
                        sightings = _extract_sightings(content)
                        created = 0
                        
                        # Better error handling in the sighting creation loop
                        for i, sight in enumerate(sightings):
                            try:
                                _create_sighting(raw_report, sight)
                                created += 1
                            except Exception as e:
                                logger.error(f"Error creating sighting {i} for {message_id}: {e}")
                                continue
                        
                        # Mark as processed
                        raw_report.processed = True
                        raw_report.save(update_fields=["processed"])
                        
                        total_files_processed += 1
                        total_sightings_created += created
                        
                        logger.info(f"File {year_folder}/{month_folder}/{filename}: created {created} sightings from {message_id}")
                    
                    # Move file to processed folder if requested
                    if move_processed:
                        processed_file_path = os.path.join(processed_folder, filename)
                        os.rename(file_path, processed_file_path)
                        logger.debug(f"Moved {filename} to processed folder")
                        
                except Exception as e:
                    logger.exception(f"Error processing file {year_folder}/{month_folder}/{filename}: {e}")
    
    logger.info(f"Processing complete! Total files: {total_files_processed}, Total sightings: {total_sightings_created}")
    if encoding_issues > 0:
        logger.warning(f"Encoding issues encountered in {encoding_issues} files")

# Convenience functions for common use cases
def process_recent_years(base_folder_path: str, years_back: int = 2):
    """Process only the most recent years of data."""
    from datetime import datetime
    current_year = datetime.now().year
    year_filter = list(range(current_year - years_back, current_year + 1))
    process_txt_files_from_nested_folders(base_folder_path, year_filter=year_filter)

def process_specific_year_month(base_folder_path: str, year: int, month: str):
    """Process a specific year and month."""
    process_txt_files_from_nested_folders(base_folder_path, year_filter=[year], month_filter=[month])

def process_year_range(base_folder_path: str, start_year: int, end_year: int):
    """Process a range of years."""
    year_filter = list(range(start_year, end_year + 1))
    process_txt_files_from_nested_folders(base_folder_path, year_filter=year_filter)



