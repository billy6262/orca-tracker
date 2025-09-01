from __future__ import annotations
import math
import random
import logging
from collections import defaultdict
from datetime import datetime, timedelta
from typing import Dict, Iterable, List, Tuple

from django.db import IntegrityError, transaction
from django.utils import timezone
from django.db.models import Min, Max

from .models import OrcaSighting, Zone, ZoneEffort, ZoneSeasonality

logger = logging.getLogger(__name__)

def _zone_adjacency_map() -> Dict[int, List[int]]:
    """
    Build a dict zoneNumber -> list of adjacent zoneNumbers.
    Assumes Zone has a many-to-many 'adjacentZones' to Zone.
    """
    zones = Zone.objects.prefetch_related("adjacentZones").only("zoneNumber")
    return {z.zoneNumber: [a.zoneNumber for a in z.adjacentZones.all()] for z in zones}


def _build_weight_caches():
    """Preload lookups so we don't hit the DB for every hour."""
    # Map zoneNumber -> Zone instance for foreign key lookup
    zones_by_number = {z.zoneNumber: z for z in Zone.objects.all()}
    
    # Effort/Seasonality keyed by Zone instance (zone foreign key)
    effort = {
        (zone, hour): float(avg)
        for (zone, hour, avg) in ZoneEffort.objects.select_related('zone').values_list('zone', 'hour', 'avg_sightings')
    }
    season = {
        (zone, month): float(avg)
        for (zone, month, avg) in ZoneSeasonality.objects.select_related('zone').values_list('zone', 'month', 'avg_sightings')
    }
    return zones_by_number, effort, season


def _zone_weights(at_time: datetime, zones_by_number: Dict[int, Zone],
                  effort: Dict[tuple, float], season: Dict[tuple, float]) -> Dict[int, float]:
    """Weight per zoneNumber using Effort(hour) * Seasonality(month); strictly positive."""
    hour, month = at_time.hour, at_time.month
    weights: Dict[int, float] = {}
    for zone_num, zone_instance in zones_by_number.items():
        e = effort.get((zone_instance, hour), 1.0)
        s = season.get((zone_instance, month), 1.0)
        w = max(e * s, 1e-6)
        weights[zone_num] = w
    return weights


def _eligible_zones_at(at_time: datetime, adj_map: Dict[int, List[int]]) -> List[int]:
    """
    Determine eligible zones at timestamp 'at_time':
      - No present=true sightings in this zone in last 2 hours
      - No present=true sightings in any adjacent zone in last 3 hours
      - No absence (present=false) already in this zone in last 3 hours
    """
    two_hours_ago = at_time - timedelta(hours=2)
    three_hours_ago = at_time - timedelta(hours=3)

    # Get zone numbers with present sightings using ZoneNumber foreign key
    zones_present_2h = set(
        OrcaSighting.objects.filter(
            present=True, 
            time__gt=two_hours_ago, 
            time__lte=at_time,
            ZoneNumber__isnull=False  # Only consider sightings with valid zones
        ).values_list("ZoneNumber__zoneNumber", flat=True).distinct()
    )
    zones_present_3h = set(
        OrcaSighting.objects.filter(
            present=True, 
            time__gt=three_hours_ago, 
            time__lte=at_time,
            ZoneNumber__isnull=False
        ).values_list("ZoneNumber__zoneNumber", flat=True).distinct()
    )

    # Zones with any absence in last 3 hours (skip to avoid duplicates)
    zones_absent_3h = set(
        OrcaSighting.objects.filter(
            present=False, 
            time__gt=three_hours_ago, 
            time__lte=at_time,
            ZoneNumber__isnull=False
        ).values_list("ZoneNumber__zoneNumber", flat=True).distinct()
    )

    eligible: List[int] = []
    for zone_num, adj_list in adj_map.items():
        # Skip if this zone had presence in last 2h
        if zone_num in zones_present_2h:
            continue

        # Skip if any adjacent zone had presence in last 3h
        if any(adj in zones_present_3h for adj in adj_list):
            continue

        # Skip if an absence exists in last 3h for this zone
        if zone_num in zones_absent_3h:
            continue

        eligible.append(zone_num)

    return eligible


def _iter_hourly_range(start: datetime, end: datetime):
    """
    Yield hourly timestamps from start (inclusive) to end (inclusive), normalized to hour.
    """
    # Normalize to start of hour
    start = start.replace(minute=0, second=0, microsecond=0)
    end = end.replace(minute=0, second=0, microsecond=0)
    t = start
    while t <= end:
        yield t
        t += timedelta(hours=1)


def _weighted_downsample_absences(target_count: int, zones_by_number: Dict[int, Zone],
                                 effort: Dict[tuple, float], season: Dict[tuple, float],
                                 progress_callback=None) -> int:
    """
    Downsample existing absence records to target_count using weighted sampling.
    Higher effort×seasonality zones have higher probability of retention.
    Returns: number of absences deleted
    """
    if target_count <= 0:
        # Delete all absences
        deleted_count = OrcaSighting.objects.filter(present=False).count()
        OrcaSighting.objects.filter(present=False).delete()
        return deleted_count
    
    # Get all absence records with their weights
    absence_qs = OrcaSighting.objects.filter(present=False).select_related('ZoneNumber')
    total_absences = absence_qs.count()
    
    if total_absences <= target_count:
        return 0  # No downsampling needed
    
    logger.info(f"Downsampling {total_absences} absences to {target_count} (removing {total_absences - target_count})")
    
    # Calculate weights for all absence records
    weighted_absences = []
    batch_size = 10000
    processed = 0
    
    for batch_start in range(0, total_absences, batch_size):
        batch = absence_qs[batch_start:batch_start + batch_size]
        
        for absence in batch:
            if absence.ZoneNumber:
                zone_instance = absence.ZoneNumber
                e = effort.get((zone_instance, absence.hour), 1.0)
                s = season.get((zone_instance, absence.month), 1.0)
                weight = max(e * s, 1e-6)
            else:
                weight = 1e-6  # Very low weight for invalid zones
            
            # Use Efraimidis–Spirakis algorithm key
            u = random.random()
            key = u ** (1.0 / weight)
            weighted_absences.append((key, absence.id))
        
        processed += len(batch)
        if progress_callback:
            progress_callback(f"Calculating weights: {processed}/{total_absences}")
    
    # Sort by key descending and keep top target_count
    weighted_absences.sort(reverse=True, key=lambda x: x[0])
    ids_to_keep = {absence_id for _, absence_id in weighted_absences[:target_count]}
    
    # Delete records not in keep set
    deleted_count = 0
    batch_size = 5000
    
    # Process deletions in batches to avoid memory issues
    all_absence_ids = set(OrcaSighting.objects.filter(present=False).values_list('id', flat=True))
    ids_to_delete = all_absence_ids - ids_to_keep
    
    for i in range(0, len(ids_to_delete), batch_size):
        batch_ids = list(ids_to_delete)[i:i + batch_size]
        batch_deleted = OrcaSighting.objects.filter(id__in=batch_ids).delete()[0]
        deleted_count += batch_deleted
        
        if progress_callback:
            progress_callback(f"Deleting absences: {i + len(batch_ids)}/{len(ids_to_delete)}")
    
    return deleted_count


def generate_absence_reports_two_phase(
    start: datetime | None = None,
    end: datetime | None = None,
    step_hours: int = 1,
    progress_callback=None,
) -> Tuple[int, int, int, int]:
    """
    Two-phase absence generation:
    Phase 1: Generate ALL eligible absence reports (ignoring ratio)
    Phase 2: Downsample to 1:3 ratio using effort×seasonality weighting
    
    Returns: (total_hour_buckets_processed, total_generated, total_kept_after_downsample, total_deleted)
    """
    # Determine historical bounds
    qs_bounds = OrcaSighting.objects.filter(present=True)
    bounds = qs_bounds.aggregate(min_t=Min("time"), max_t=Max("time"))
    min_time = bounds["min_t"]
    max_time = bounds["max_t"]

    if not min_time or not max_time:
        return (0, 0, 0, 0)  # no data

    # Use provided range or fall back to all-time range
    start = start or min_time
    end = end or max_time

    # Ensure tz-aware
    if timezone.is_naive(start):
        start = timezone.make_aware(start, timezone.get_current_timezone())
    if timezone.is_naive(end):
        end = timezone.make_aware(end, timezone.get_current_timezone())

    # Prepare iteration plan
    hours = list(_iter_hourly_range(start, end))
    if step_hours != 1:
        hours = hours[::max(1, int(step_hours))]
    total_buckets = len(hours)
    if total_buckets == 0:
        return (0, 0, 0, 0)

    zones_by_number, EFFORT, SEASON = _build_weight_caches()
    adj_map = _zone_adjacency_map()
    
    logger.info(f"Phase 1: Generating all eligible absences for {total_buckets} hour buckets")
    
    # PHASE 1: Generate ALL eligible absences (no ratio constraint)
    created_total = 0
    
    for idx, ts in enumerate(hours):
        if progress_callback and idx % 100 == 0:
            progress_callback(f"Phase 1: Processing hour {idx + 1}/{total_buckets} ({ts.strftime('%Y-%m-%d %H:%M')})")
        
        candidates = _eligible_zones_at(ts, adj_map)
        if not candidates:
            continue

        # Generate absences for ALL eligible zones (no sampling)
        is_weekend = ts.weekday() >= 5
        objs: List[OrcaSighting] = []
        
        for zn in candidates:
            zone_instance = zones_by_number.get(zn)
            if not zone_instance:
                continue  # Skip if zone not found
                
            objs.append(
                OrcaSighting(
                    raw_report=None,
                    time=ts,
                    zone=str(zn),
                    ZoneNumber=zone_instance,
                    direction="none",
                    count=0,
                    month=ts.month,
                    dayOfWeek=ts.isoweekday(),
                    hour=ts.hour,
                    reportsIn5h=None,
                    reportsIn24h=None,
                    reportsInAdjacentZonesIn5h=None,
                    reportsInAdjacentPlusZonesIn5h=None,
                    present=False,
                    timeSinceLastSighting=None,
                    isWeekend=is_weekend,
                    sunUp=None,
                )
            )

        # Insert in batches
        if objs:
            batch_size = 1000
            created_here = 0
            for i in range(0, len(objs), batch_size):
                chunk = objs[i : i + batch_size]
                res = OrcaSighting.objects.bulk_create(chunk, ignore_conflicts=True)
                created_here += len(res)
            
            created_total += created_here

    if progress_callback:
        progress_callback(f"Phase 1 complete: Generated {created_total} absence records")

    # PHASE 2: Downsample to achieve 1:3 ratio
    total_present = OrcaSighting.objects.filter(present=True).count()
    target_absent = 3 * total_present
    current_absent = OrcaSighting.objects.filter(present=False).count()
    
    logger.info(f"Phase 2: Downsampling {current_absent} absences to {target_absent} (1:3 ratio)")
    
    if progress_callback:
        progress_callback(f"Phase 2: Downsampling {current_absent} to {target_absent}")
    
    deleted_count = _weighted_downsample_absences(
        target_absent, zones_by_number, EFFORT, SEASON, progress_callback
    )
    
    final_absent_count = current_absent - deleted_count
    
    if progress_callback:
        progress_callback(f"Complete: {final_absent_count} absences kept, {deleted_count} deleted")
    
    return (total_buckets, created_total, final_absent_count, deleted_count)


# Keep original function for backward compatibility
def generate_absence_reports_historical(
    start: datetime | None = None,
    end: datetime | None = None,
    step_hours: int = 1,
) -> Tuple[int, int, int]:
    """
    Legacy function - now calls two-phase generation.
    Returns: (total_hour_buckets_processed, total_selected, total_created)
    """
    buckets, generated, kept, deleted = generate_absence_reports_two_phase(
        start, end, step_hours
    )
    return (buckets, generated, kept)