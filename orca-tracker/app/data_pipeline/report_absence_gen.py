from __future__ import annotations
import math
import random
from collections import defaultdict
from datetime import datetime, timedelta
from typing import Dict, Iterable, List, Tuple

from django.db import IntegrityError, transaction
from django.utils import timezone
from django.db.models import Min, Max

from .models import OrcaSighting, Zone, ZoneEffort, ZoneSeasonality


def _zone_adjacency_map() -> Dict[int, List[int]]:
    """
    Build a dict zoneNumber -> list of adjacent zoneNumbers.
    Assumes Zone has a many-to-many 'adjacentZones' to Zone.
    """
    zones = Zone.objects.prefetch_related("adjacentZones").only("zoneNumber")
    return {z.zoneNumber: [a.zoneNumber for a in z.adjacentZones.all()] for z in zones}


def _build_weight_caches():
    """Preload lookups so we don't hit the DB for every hour."""
    # Map zoneNumber -> Zone.pk
    zone_id_by_number = dict(Zone.objects.values_list('zoneNumber', 'id'))
    # Effort/Seasonality keyed by Zone.pk
    effort = {
        (zid, hour): float(avg)
        for (zid, hour, avg) in ZoneEffort.objects.values_list('zone_id', 'hour', 'avg_sightings')
    }
    season = {
        (zid, month): float(avg)
        for (zid, month, avg) in ZoneSeasonality.objects.values_list('zone_id', 'month', 'avg_sightings')
    }
    return zone_id_by_number, effort, season


def _zone_weights(at_time: datetime, zone_id_by_number: Dict[int, int],
                  effort: Dict[tuple, float], season: Dict[tuple, float]) -> Dict[int, float]:
    """Weight per zoneNumber using Effort(hour) * Seasonality(month); strictly positive."""
    hour, month = at_time.hour, at_time.month
    weights: Dict[int, float] = {}
    for zn, zid in zone_id_by_number.items():
        e = effort.get((zid, hour), 1.0)
        s = season.get((zid, month), 1.0)
        w = max(e * s, 1e-6)
        weights[zn] = w
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

    # Zones with present sightings in lookback windows
    zones_present_2h = set(
        OrcaSighting.objects.filter(
            present=True, time__gt=two_hours_ago, time__lte=at_time
        ).values_list("zone", flat=True).distinct()
    )
    zones_present_3h = set(
        OrcaSighting.objects.filter(
            present=True, time__gt=three_hours_ago, time__lte=at_time
        ).values_list("zone", flat=True).distinct()
    )

    # Zones with any absence in last 3 hours (skip to avoid duplicates)
    zones_absent_3h = set(
        OrcaSighting.objects.filter(
            present=False, time__gt=three_hours_ago, time__lte=at_time
        ).values_list("zone", flat=True).distinct()
    )

    eligible: List[int] = []
    for zone_num, adj_list in adj_map.items():
        zs = str(zone_num)

        # Skip if this zone had presence in last 2h
        if zs in zones_present_2h:
            continue

        # Skip if any adjacent zone had presence in last 3h
        if any(str(adj) in zones_present_3h for adj in adj_list):
            continue

        # Skip if an absence exists in last 3h for this zone
        if zs in zones_absent_3h:
            continue

        eligible.append(zone_num)

    return eligible


def _pick_weighted(candidates: List[int], weights: Dict[int, float], k: int) -> List[int]:
    """
    Weighted sampling without replacement (Efraimidis–Spirakis):
    key_i = U_i ** (1 / w_i); pick top-k by key descending.
    """
    if k <= 0 or not candidates:
        return []
    keys = []
    for zn in candidates:
        w = max(weights.get(zn, 1.0), 1e-9)
        u = random.random()
        key = u ** (1.0 / w)
        keys.append((key, zn))
    keys.sort(reverse=True)
    return [zn for _, zn in keys[:k]]


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


def generate_absence_reports_historical(
    start: datetime | None = None,
    end: datetime | None = None,
    step_hours: int = 1,
) -> Tuple[int, int, int]:
    """
    Generate absence reports across history in hourly buckets.

    Rules:
      - presence=False
      - Only consider presence=True sightings for eligibility checks
      - Eligibility per timestamp T requires:
          * No same-zone presence in (T-2h, T]
          * No adjacent-zone presence in (T-3h, T]
          * No existing absence in same zone in (T-3h, T]
      - Leave recency fields and sunUp as NULL
      - Enforce uniqueness: one absence per zone per hour (DB UniqueConstraint)
      - Maintain global 1:3 (sightings:absences) ratio via weighted downsampling (effort × seasonality)

    Returns: (total_hour_buckets_processed, total_selected, total_created)
    """
    # Determine historical bounds if not provided (use all-time present sightings as baseline)
    qs_bounds = OrcaSighting.objects.filter(present=True)
    bounds = qs_bounds.aggregate(min_t=Min("time"), max_t=Max("time"))
    min_time = bounds["min_t"]
    max_time = bounds["max_t"]

    if not min_time or not max_time:
        return (0, 0, 0)  # no data

    # Use provided range or fall back to all-time range
    start = start or min_time
    end = end or max_time

    # Ensure tz-aware
    if timezone.is_naive(start):
        start = timezone.make_aware(start, timezone.get_current_timezone())
    if timezone.is_naive(end):
        end = timezone.make_aware(end, timezone.get_current_timezone())

    # Precompute global targets
    total_present_all = OrcaSighting.objects.filter(present=True).count()
    total_absent_existing = OrcaSighting.objects.filter(present=False).count()
    target_absent = 3 * total_present_all
    remaining_to_create = max(0, target_absent - total_absent_existing)
    if remaining_to_create == 0:
        return (0, 0, 0)

    # Prepare iteration plan
    hours = list(_iter_hourly_range(start, end))
    if step_hours != 1:
        hours = hours[::max(1, int(step_hours))]
    total_buckets = len(hours)
    if total_buckets == 0:
        return (0, 0, 0)

    zone_id_by_number, EFFORT, SEASON = _build_weight_caches()
    adj_map = _zone_adjacency_map()
    created_total = 0
    selected_total = 0

    # Process chronologically; allocate a per-bucket cap so we converge on the target
    for idx, ts in enumerate(hours):
        # Recompute remaining each loop (in case some rows failed/ignored due to uniqueness)
        remaining_buckets = total_buckets - idx
        if remaining_to_create <= 0:
            break

        # Per-bucket cap to spread creation across timeline
        per_bucket_cap = math.ceil(remaining_to_create / max(1, remaining_buckets))

        candidates = _eligible_zones_at(ts, adj_map)
        if not candidates:
            continue

        weights = _zone_weights(ts, zone_id_by_number, EFFORT, SEASON)
        k = min(per_bucket_cap, len(candidates))
        selected = _pick_weighted(candidates, weights, k)
        selected_total += len(selected)

        if not selected:
            continue

        # Build absence rows at timestamp ts
        is_weekend = ts.weekday() >= 5
        objs: List[OrcaSighting] = []
        for zn in selected:
            objs.append(
                OrcaSighting(
                    raw_report=None,        # no raw report for absence
                    time=ts,                # historical timestamp (bucket)
                    zone=str(zn),
                    direction="none",
                    count=0,
                    month=ts.month,
                    dayOfWeek=ts.isoweekday(),
                    hour=ts.hour,
                    # Recency and sunUp left blank
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

        # Insert in batches; ignore_conflicts to honor uniqueness constraint
        created_here = 0
        batch = 500
        for i in range(0, len(objs), batch):
            chunk = objs[i : i + batch]
            res = OrcaSighting.objects.bulk_create(chunk, ignore_conflicts=True)
            created_here += len(res)

        created_total += created_here
        remaining_to_create -= created_here

    return (total_buckets, selected_total, created_total)