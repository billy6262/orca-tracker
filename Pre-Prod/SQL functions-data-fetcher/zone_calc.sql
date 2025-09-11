BEGIN;  --run to force update all rows "docker compose exec -T db psql -U orca -d orca_tracker -c 'UPDATE "data_pipeline_orcasighting" SET "zone"="zone";'"

-- Indexes
CREATE INDEX IF NOT EXISTS idx_orcasighting_zone_time
  ON "data_pipeline_orcasighting" ("zone","time");
CREATE INDEX IF NOT EXISTS idx_orcasighting_zoneint_time
  ON "data_pipeline_orcasighting" (((("zone")::int)), "time");
CREATE INDEX IF NOT EXISTS idx_orcasighting_zone_time_present_true
  ON "data_pipeline_orcasighting" ("zone","time")
  WHERE "present" IS TRUE;
CREATE INDEX IF NOT EXISTS idx_orcasighting_zoneint_time_present_true
  ON "data_pipeline_orcasighting" (((("zone")::int)), "time")
  WHERE "present" IS TRUE;

CREATE OR REPLACE FUNCTION public.fn_update_orcasighting_recency()
RETURNS trigger
LANGUAGE plpgsql
AS $$
DECLARE
  zone_num integer;
  m integer;
  t_local time;
  sunrise time;
  sunset time;
  last_sighting_time timestamp with time zone;
BEGIN
  -- Normalize zone number
  BEGIN
    zone_num := NEW."zone"::int;
  EXCEPTION WHEN invalid_text_representation THEN
    zone_num := NULL;
  END;

  -- Calculate sunUp flag for ALL records
  IF NEW."time" IS NOT NULL THEN
    m := EXTRACT(MONTH FROM NEW."time")::int;
    t_local := (NEW."time")::time;

    CASE m
      WHEN 1 THEN sunrise := TIME '08:00'; sunset := TIME '16:30';
      WHEN 2 THEN sunrise := TIME '07:30'; sunset := TIME '17:30';
      WHEN 3 THEN sunrise := TIME '07:00'; sunset := TIME '19:15';
      WHEN 4 THEN sunrise := TIME '06:30'; sunset := TIME '20:00';
      WHEN 5 THEN sunrise := TIME '05:30'; sunset := TIME '20:45';
      WHEN 6 THEN sunrise := TIME '05:10'; sunset := TIME '21:05';
      WHEN 7 THEN sunrise := TIME '05:20'; sunset := TIME '20:55';
      WHEN 8 THEN sunrise := TIME '05:50'; sunset := TIME '20:20';
      WHEN 9 THEN sunrise := TIME '06:35'; sunset := TIME '19:25';
      WHEN 10 THEN sunrise := TIME '07:10'; sunset := TIME '18:20';
      WHEN 11 THEN sunrise := TIME '07:50'; sunset := TIME '16:40';
      WHEN 12 THEN sunrise := TIME '08:05'; sunset := TIME '16:20';
      ELSE  sunrise := TIME '08:00'; sunset := TIME '17:00';
    END CASE;

    -- Expand daylight window: sunrise 30m earlier, sunset 30m later to account for twilight
    sunrise := sunrise - INTERVAL '30 minutes';
    sunset  := sunset  + INTERVAL '30 minutes';

    NEW."sunUp" := (t_local >= sunrise AND t_local < sunset);
  END IF;

  -- Calculate time since last sighting for ALL records (only counts present=TRUE sightings)
  SELECT MAX(os."time") INTO last_sighting_time
  FROM "data_pipeline_orcasighting" os
  WHERE os."zone" = NEW."zone"
    AND os."present" IS TRUE
    AND os."time" < NEW."time"
    AND (os."id" IS DISTINCT FROM NEW."id");  -- Exclude self

  IF last_sighting_time IS NOT NULL THEN
    NEW."timeSinceLastSighting" := NEW."time" - last_sighting_time;
  ELSE
    -- No previous sighting found, leave NULL
    NEW."timeSinceLastSighting" := NULL;
  END IF;

  -- Calculate recency windows for ALL records
  -- 6h window: [t-6h, t+1h)
  SELECT COUNT(*) INTO NEW."reportsIn5h"
  FROM "data_pipeline_orcasighting" os
  WHERE os."zone" = NEW."zone"
    AND os."present" IS TRUE  -- Only count present sightings
    AND os."time" >= NEW."time" - INTERVAL '6 hours'
    AND os."time" <  NEW."time" + INTERVAL '1 hour'
    AND (os."id" IS DISTINCT FROM NEW."id");

  -- 25h window: [t-25h, t+1h)
  SELECT COUNT(*) INTO NEW."reportsIn24h"
  FROM "data_pipeline_orcasighting" os
  WHERE os."zone" = NEW."zone"
    AND os."present" IS TRUE  -- Only count present sightings
    AND os."time" >= NEW."time" - INTERVAL '25 hours'
    AND os."time" <  NEW."time" + INTERVAL '1 hour'
    AND (os."id" IS DISTINCT FROM NEW."id");

  -- Handle adjacent zone calculations for ALL records
  IF zone_num IS NULL THEN
    NEW."reportsInAdjacentZonesIn5h" := 0;
    NEW."reportsInAdjacentPlusZonesIn5h" := 0;
  ELSE
    -- Adjacent 6h window: [t-6h, t+1h) - only counts present=TRUE sightings
    SELECT COUNT(*) INTO NEW."reportsInAdjacentZonesIn5h"
    FROM "data_pipeline_orcasighting" os
    WHERE os."present" IS TRUE  -- Only count present sightings
      AND os."time" >= NEW."time" - INTERVAL '6 hours'
      AND os."time" <  NEW."time" + INTERVAL '1 hour'
      AND (os."id" IS DISTINCT FROM NEW."id")
      AND (os."zone")::int IN (
        SELECT az."to_zone_id"
        FROM "data_pipeline_zone_adjacentZones" az
        WHERE az."from_zone_id" = zone_num
      );

    -- Next-adjacent 6h window: [t-6h, t+1h) - only counts present=TRUE sightings
    SELECT COUNT(*) INTO NEW."reportsInAdjacentPlusZonesIn5h"
    FROM "data_pipeline_orcasighting" os
    WHERE os."present" IS TRUE  -- Only count present sightings
      AND os."time" >= NEW."time" - INTERVAL '6 hours'
      AND os."time" <  NEW."time" + INTERVAL '1 hour'
      AND (os."id" IS DISTINCT FROM NEW."id")
      AND (os."zone")::int IN (
        SELECT naz."to_zone_id"
        FROM "data_pipeline_zone_nextAdjacentZones" naz
        WHERE naz."from_zone_id" = zone_num
      );
  END IF;

  RETURN NEW;
END;
$$;

-- Triggers
DROP TRIGGER IF EXISTS trg_orcasighting_recency_ins ON "data_pipeline_orcasighting";
CREATE TRIGGER trg_orcasighting_recency_ins
BEFORE INSERT ON "data_pipeline_orcasighting"
FOR EACH ROW
EXECUTE FUNCTION public.fn_update_orcasighting_recency();

DROP TRIGGER IF EXISTS trg_orcasighting_recency_upd ON "data_pipeline_orcasighting";
CREATE TRIGGER trg_orcasighting_recency_upd
BEFORE UPDATE OF "time","zone" ON "data_pipeline_orcasighting"
FOR EACH ROW
EXECUTE FUNCTION public.fn_update_orcasighting_recency();

COMMIT;