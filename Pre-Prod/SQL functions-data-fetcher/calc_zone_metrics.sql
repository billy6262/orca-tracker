BEGIN;

-- Function to update ZoneSeasonality for a specific zone/month
CREATE OR REPLACE FUNCTION fn_update_zone_seasonality(p_zone_number int, p_month int)
RETURNS void
LANGUAGE plpgsql
AS $$
DECLARE
  avg_sightings_val float;
BEGIN
  -- Calculate average sightings per calendar day for this zone/month
  WITH monthly AS (
    SELECT
      DATE_TRUNC('month', s."time") AS month_start,
      COUNT(*)::bigint AS sightings_in_month,
      (
        (DATE_TRUNC('month', s."time") + INTERVAL '1 month - 1 day')::date
        - DATE_TRUNC('month', s."time")::date + 1
      ) AS days_in_month
    FROM "data_pipeline_orcasighting" s
    WHERE s."present" IS TRUE
      AND s."zone" ~ '^[0-9]+$'
      AND s."zone"::int = p_zone_number
      AND EXTRACT(MONTH FROM s."time")::int = p_month
    GROUP BY DATE_TRUNC('month', s."time")
  )
  SELECT COALESCE(
    SUM(sightings_in_month)::float / NULLIF(SUM(days_in_month), 0),
    0.0
  ) INTO avg_sightings_val
  FROM monthly;

  -- Insert or update the seasonality record
  INSERT INTO "data_pipeline_zoneseasonality" ("zone_id", "month", "avg_sightings")
  VALUES (p_zone_number, p_month, avg_sightings_val)
  ON CONFLICT ("zone_id", "month")
  DO UPDATE SET "avg_sightings" = EXCLUDED."avg_sightings";
END;
$$;

-- Function to update ZoneEffort for a specific zone/hour
CREATE OR REPLACE FUNCTION fn_update_zone_effort(p_zone_number int, p_hour int)
RETURNS void
LANGUAGE plpgsql
AS $$
DECLARE
  avg_sightings_val float;
BEGIN
  -- Calculate average sightings per day for this zone/hour
  WITH hourly_daily AS (
    SELECT
      s."time"::date AS day,
      COUNT(*)::int AS sightings
    FROM "data_pipeline_orcasighting" s
    WHERE s."present" IS TRUE
      AND s."zone" ~ '^[0-9]+$'
      AND s."zone"::int = p_zone_number
      AND EXTRACT(HOUR FROM s."time")::int = p_hour
    GROUP BY s."time"::date
  )
  SELECT COALESCE(AVG(sightings)::float, 0.0) INTO avg_sightings_val
  FROM hourly_daily;

  -- Insert or update the effort record
  INSERT INTO "data_pipeline_zoneeffort" ("zone_id", "hour", "avg_sightings")
  VALUES (p_zone_number, p_hour, avg_sightings_val)
  ON CONFLICT ("zone_id", "hour")
  DO UPDATE SET "avg_sightings" = EXCLUDED."avg_sightings";
END;
$$;

-- Trigger function for OrcaSighting changes
CREATE OR REPLACE FUNCTION fn_update_zone_metrics()
RETURNS trigger
LANGUAGE plpgsql
AS $$
DECLARE
  zone_num_old int;
  zone_num_new int;
  month_old int;
  month_new int;
  hour_old int;
  hour_new int;
BEGIN
  -- Handle INSERT
  IF TG_OP = 'INSERT' THEN
    IF NEW."present" IS TRUE AND NEW."zone" ~ '^[0-9]+$' THEN
      zone_num_new := NEW."zone"::int;
      month_new := EXTRACT(MONTH FROM NEW."time")::int;
      hour_new := EXTRACT(HOUR FROM NEW."time")::int;
      
      PERFORM fn_update_zone_seasonality(zone_num_new, month_new);
      PERFORM fn_update_zone_effort(zone_num_new, hour_new);
    END IF;
    RETURN NEW;
  END IF;

  -- Handle DELETE
  IF TG_OP = 'DELETE' THEN
    IF OLD."present" IS TRUE AND OLD."zone" ~ '^[0-9]+$' THEN
      zone_num_old := OLD."zone"::int;
      month_old := EXTRACT(MONTH FROM OLD."time")::int;
      hour_old := EXTRACT(HOUR FROM OLD."time")::int;
      
      PERFORM fn_update_zone_seasonality(zone_num_old, month_old);
      PERFORM fn_update_zone_effort(zone_num_old, hour_old);
    END IF;
    RETURN OLD;
  END IF;

  -- Handle UPDATE
  IF TG_OP = 'UPDATE' THEN
    IF OLD."present" IS TRUE AND OLD."zone" ~ '^[0-9]+$' THEN
      zone_num_old := OLD."zone"::int;
      month_old := EXTRACT(MONTH FROM OLD."time")::int;
      hour_old := EXTRACT(HOUR FROM OLD."time")::int;
      
      PERFORM fn_update_zone_seasonality(zone_num_old, month_old);
      PERFORM fn_update_zone_effort(zone_num_old, hour_old);
    END IF;
    
    IF NEW."present" IS TRUE AND NEW."zone" ~ '^[0-9]+$' THEN
      zone_num_new := NEW."zone"::int;
      month_new := EXTRACT(MONTH FROM NEW."time")::int;
      hour_new := EXTRACT(HOUR FROM NEW."time")::int;
      
      PERFORM fn_update_zone_seasonality(zone_num_new, month_new);
      PERFORM fn_update_zone_effort(zone_num_new, hour_new);
    END IF;
    
    RETURN NEW;
  END IF;

  RETURN NULL;
END;
$$;

-- Create the trigger
DROP TRIGGER IF EXISTS trg_orcasighting_zone_metrics ON "data_pipeline_orcasighting";
CREATE TRIGGER trg_orcasighting_zone_metrics
AFTER INSERT OR UPDATE OR DELETE ON "data_pipeline_orcasighting"
FOR EACH ROW
EXECUTE FUNCTION fn_update_zone_metrics();

-- Add unique constraints 
DO $$
BEGIN
    -- Add seasonality constraint if it doesn't exist
    IF NOT EXISTS (
        SELECT 1 FROM pg_constraint 
        WHERE conname = 'uq_seasonality_zone_month'
    ) THEN
        ALTER TABLE "data_pipeline_zoneseasonality" 
        ADD CONSTRAINT uq_seasonality_zone_month 
        UNIQUE ("zone_id", "month");
    END IF;
    
    -- Add effort constraint if it doesn't exist
    IF NOT EXISTS (
        SELECT 1 FROM pg_constraint 
        WHERE conname = 'uq_effort_zone_hour'
    ) THEN
        ALTER TABLE "data_pipeline_zoneeffort" 
        ADD CONSTRAINT uq_effort_zone_hour 
        UNIQUE ("zone_id", "hour");
    END IF;
END $$;

COMMIT;