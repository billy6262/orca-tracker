BEGIN;  --"docker compose exec -T db psql -U orca -d orca_tracker -c 'UPDATE "data_pipeline_orcasighting" SET "zone"="zone";'"

-- Indexes for performance (works even if zone is stored as text)
CREATE INDEX IF NOT EXISTS idx_orcasighting_zone_time
  ON "data_pipeline_orcasighting" ("zone","time");
-- Functional index to support casts in adjacency queries
CREATE INDEX IF NOT EXISTS idx_orcasighting_zoneint_time
  ON "data_pipeline_orcasighting" (((("zone")::int)), "time");

CREATE OR REPLACE FUNCTION public.fn_update_orcasighting_recency()
RETURNS trigger
LANGUAGE plpgsql
AS $$
DECLARE
  zone_num integer;
BEGIN
  -- Normalize zone number (in case column is text)
  BEGIN
    zone_num := NEW."zone"::int;
  EXCEPTION WHEN invalid_text_representation THEN
    zone_num := NULL;
  END;

  -- Same-zone counts (exclude the new row by using [t-5h, t) and [t-24h, t))
  SELECT COUNT(*)
    INTO NEW."reportsIn5h"
  FROM "data_pipeline_orcasighting" os
  WHERE os."zone" = NEW."zone"
    AND os."time" >= NEW."time" - INTERVAL '5 hours'
    AND os."time" <  NEW."time";

  SELECT COUNT(*)
    INTO NEW."reportsIn24h"
  FROM "data_pipeline_orcasighting" os
  WHERE os."zone" = NEW."zone"
    AND os."time" >= NEW."time" - INTERVAL '24 hours'
    AND os."time" <  NEW."time";

  IF zone_num IS NULL THEN
    NEW."reportsInAdjacentZonesIn5h" := 0;
    NEW."reportsInAdjacentPlusZonesIn5h" := 0;
    RETURN NEW;
  END IF;

  -- Immediate adjacent zones in past 5h (exclude same-zone)
  SELECT COUNT(*)
    INTO NEW."reportsInAdjacentZonesIn5h"
  FROM "data_pipeline_orcasighting" os
  WHERE os."time" >= NEW."time" - INTERVAL '5 hours'
    AND os."time" <  NEW."time"
    AND (os."zone")::int IN (
      SELECT az."to_zone_id"
      FROM "data_pipeline_zone_adjacentZones" az
      WHERE az."from_zone_id" = zone_num
    );

  -- Next-adjacent zones in past 5h
  SELECT COUNT(*)
    INTO NEW."reportsInAdjacentPlusZonesIn5h"
  FROM "data_pipeline_orcasighting" os
  WHERE os."time" >= NEW."time" - INTERVAL '5 hours'
    AND os."time" <  NEW."time"
    AND (os."zone")::int IN (
      SELECT naz."to_zone_id"
      FROM "data_pipeline_zone_nextAdjacentZones" naz
      WHERE naz."from_zone_id" = zone_num
    );

  RETURN NEW;
END;
$$;

-- Triggers for inserts and for updates when time/zone change
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