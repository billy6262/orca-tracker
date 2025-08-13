import os
import logging
from typing import List, Dict, Any
from dateutil import parser as dtparser
from django.db import transaction
import openai
from .models import RawReport, OrcaSighting

logger = logging.getLogger(__name__)

MODEL_NAME = os.getenv("OPENAI_MODEL", "gpt-4o-mini")

# Global client variable - will be initialized when needed
_client = None

def get_openai_api_key():
    """Get OpenAI API key from secrets folder or environment variables."""
    # First try to read from secrets folder
    # Check if running in Docker (secrets mounted at /secrets)
    if os.path.exists('/secrets/openai_api_key.txt'):
        api_key_path = '/secrets/openai_api_key.txt'
    else:
        # Local development - secrets folder in parent directory
        base_dir = os.path.dirname(os.path.dirname(os.path.dirname(__file__)))
        api_key_path = os.path.join(base_dir, 'secrets', 'openai_api_key.txt')
    
    if os.path.exists(api_key_path):
        with open(api_key_path, 'r') as f:
            return f.read().strip()
    
    # Fallback to environment variable
    api_key = os.getenv('OPENAI_API_KEY')
    if api_key:
        return api_key
    
    raise ValueError("OpenAI API key not found in secrets folder or environment variables")

def get_openai_client():
    """Get or create OpenAI client instance."""
    global _client
    if _client is None:
        _client = openai.OpenAI(api_key=get_openai_api_key())
    return _client

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
- Convert all times to ISO 8601; if date missing assume today's date in reporter's apparent timezone, else leave; (the backend may adjust later).
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
    try:
        dt = dtparser.parse(data["time"])
    except Exception:
        logger.warning(f"Could not parse time '{data.get('time')}' for report {raw.messageId}")
        return
    month, dow, hour = _calc_derived_fields(dt)
    count = _coerce_int(data.get("count"))
    if count is None or count < 0:
        return
    OrcaSighting.objects.create(
        raw_report=raw,  # Fixed field name from rawReport to raw_report
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

def _extract_sightings(body: str) -> List[Dict[str, Any]]:
    if not body.strip():
        return []
    
    try:
        client = get_openai_client()  # Get client when needed
        response = client.chat.completions.create(
            model=MODEL_NAME,
            messages=[{"role": "user", "content": PROMPT_TEMPLATE.format(body=body)}],
            response_format={
                "type": "json_schema",
                "json_schema": JSON_SCHEMA
            },
            temperature=0
        )
        
        import json
        parsed = json.loads(response.choices[0].message.content)
        return parsed.get("sightings", [])
        
    except Exception as e:
        logger.error(f"Failed to extract sightings: {e}")
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

def process_txt_files_from_folder(folder_path: str, move_processed: bool = True):
    """
    Process all .txt files in a folder as raw reports.
    
    Args:
        folder_path: Path to folder containing .txt files
        move_processed: If True, move processed files to 'processed' subfolder
    """
    if not os.path.exists(folder_path):
        logger.error(f"Folder does not exist: {folder_path}")
        return
    
    # Create processed subfolder if needed
    processed_folder = os.path.join(folder_path, "processed")
    if move_processed and not os.path.exists(processed_folder):
        os.makedirs(processed_folder)
    
    txt_files = [f for f in os.listdir(folder_path) if f.lower().endswith('.txt')]
    
    if not txt_files:
        logger.info(f"No .txt files found in {folder_path}")
        return
    
    logger.info(f"Processing {len(txt_files)} txt files from {folder_path}")
    
    for filename in txt_files:
        file_path = os.path.join(folder_path, filename)
        
        try:
            # Read file content
            with open(file_path, 'r', encoding='utf-8') as f:
                content = f.read()
            
            # Use filename (without extension) as messageId
            message_id = f"txt_file_{os.path.splitext(filename)[0]}"
            
            # Check if already processed
            if RawReport.objects.filter(messageId=message_id).exists():
                logger.info(f"File {filename} already processed, skipping")
                continue
            
            # Create RawReport entry
            with transaction.atomic():
                raw_report = RawReport.objects.create(
                    messageId=message_id,
                    subject=f"Text file: {filename}",
                    sender="txt_file_import",
                    body=content,
                    processed=False
                )
                
                # Extract sightings
                sightings = _extract_sightings(content)
                created = 0
                
                for sight in sightings:
                    _create_sighting(raw_report, sight)
                    created += 1
                
                # Mark as processed
                raw_report.processed = True
                raw_report.save(update_fields=["processed"])
                
                logger.info(f"File {filename}: created {created} sightings from {message_id}")
            
            # Move file to processed folder if requested
            if move_processed:
                processed_file_path = os.path.join(processed_folder, filename)
                os.rename(file_path, processed_file_path)
                logger.info(f"Moved {filename} to processed folder")
                
        except Exception as e:
            logger.exception(f"Error processing file {filename}: {e}")

if __name__ == "__main__":
    # Simple manual test (not typical in Django deployment)
    process_unprocessed_reports()

