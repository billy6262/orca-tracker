BEGIN;  --"docker compose exec -T db psql -U orca -d orca_tracker -c 'UPDATE "data_pipeline_orcasighting" SET "zone"="zone";'"

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
BEGIN
  -- Normalize zone number (ok even if present=false)
  BEGIN
    zone_num := NEW."zone"::int;
  EXCEPTION WHEN invalid_text_representation THEN
    zone_num := NULL;
  END;

  IF NEW."present" IS TRUE THEN
    -- sunUp by month (local time assumed)
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

      NEW."sunUp" := (t_local >= sunrise AND t_local < sunset);
    END IF;

    -- Recency windows expanded by 30 min on both sides
    SELECT COUNT(*) INTO NEW."reportsIn5h"
    FROM "data_pipeline_orcasighting" os
    WHERE os."zone" = NEW."zone"
      AND os."present" IS TRUE
      AND os."time" >= NEW."time" - INTERVAL '5 hours 30 minutes'
      AND os."time" <  NEW."time" + INTERVAL '30 minutes'
      AND (os."id" IS DISTINCT FROM NEW."id");

    SELECT COUNT(*) INTO NEW."reportsIn24h"
    FROM "data_pipeline_orcasighting" os
    WHERE os."zone" = NEW."zone"
      AND os."present" IS TRUE
      AND os."time" >= NEW."time" - INTERVAL '24 hours 30 minutes'
      AND os."time" <  NEW."time" + INTERVAL '30 minutes'
      AND (os."id" IS DISTINCT FROM NEW."id");

    IF zone_num IS NULL THEN
      NEW."reportsInAdjacentZonesIn5h" := 0;
      NEW."reportsInAdjacentPlusZonesIn5h" := 0;
      RETURN NEW;
    END IF;

    SELECT COUNT(*) INTO NEW."reportsInAdjacentZonesIn5h"
    FROM "data_pipeline_orcasighting" os
    WHERE os."present" IS TRUE
      AND os."time" >= NEW."time" - INTERVAL '5 hours 30 minutes'
      AND os."time" <  NEW."time" + INTERVAL '30 minutes'
      AND (os."id" IS DISTINCT FROM NEW."id")
      AND (os."zone")::int IN (
        SELECT az."to_zone_id"
        FROM "data_pipeline_zone_adjacentZones" az
        WHERE az."from_zone_id" = zone_num
      );

    SELECT COUNT(*) INTO NEW."reportsInAdjacentPlusZonesIn5h"
    FROM "data_pipeline_orcasighting" os
    WHERE os."present" IS TRUE
      AND os."time" >= NEW."time" - INTERVAL '5 hours 30 minutes'
      AND os."time" <  NEW."time" + INTERVAL '30 minutes'
      AND (os."id" IS DISTINCT FROM NEW."id")
      AND (os."zone")::int IN (
        SELECT naz."to_zone_id"
        FROM "data_pipeline_zone_nextAdjacentZones" naz
        WHERE naz."from_zone_id" = zone_num
      );
  ELSE
    -- Absence rows: leave recency and sunUp blank
    NEW."reportsIn5h" := NULL;
    NEW."reportsIn24h" := NULL;
    NEW."reportsInAdjacentZonesIn5h" := NULL;
    NEW."reportsInAdjacentPlusZonesIn5h" := NULL;
    NEW."sunUp" := NULL;
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