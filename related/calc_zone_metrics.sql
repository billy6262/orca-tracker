BEGIN;

-- Seasonality: average sightings per calendar day by (zone, month)
TRUNCATE TABLE "data_pipeline_zoneseasonality";

WITH monthly AS (
  SELECT
    z."zoneNumber"                                  AS zone_id,
    EXTRACT(MONTH FROM s."time")::int               AS month,
    DATE_TRUNC('month', s."time")                   AS month_start,
    COUNT(*)::bigint                                AS sightings_in_month,
    (
      (DATE_TRUNC('month', s."time") + INTERVAL '1 month - 1 day')::date
      - DATE_TRUNC('month', s."time")::date + 1
    )                                               AS days_in_month
  FROM "data_pipeline_orcasighting" s
  JOIN "data_pipeline_zone" z
    ON z."zoneNumber" = s."zone"::int
  WHERE s."present" IS TRUE
    AND s."zone" ~ '^[0-9]+$'  -- ensure numeric before cast
  GROUP BY z."zoneNumber", EXTRACT(MONTH FROM s."time"), DATE_TRUNC('month', s."time")
),
agg AS (
  -- Average per calendar day across all years for that month
  SELECT
    zone_id,
    month,
    SUM(sightings_in_month)::float / NULLIF(SUM(days_in_month), 0) AS avg_sightings
  FROM monthly
  GROUP BY zone_id, month
)
INSERT INTO "data_pipeline_zoneseasonality" ("zone_id", "month", "avg_sightings")
SELECT zone_id, month, COALESCE(avg_sightings, 0.0)
FROM agg
ORDER BY zone_id, month;

-- Effort: average sightings per day by (zone, hour-of-day)
TRUNCATE TABLE "data_pipeline_zoneeffort";

WITH hourly_daily AS (
  SELECT
    z."zoneNumber"                    AS zone_id,
    EXTRACT(HOUR FROM s."time")::int  AS hour,
    s."time"::date                    AS day,
    COUNT(*)::int                     AS sightings
  FROM "data_pipeline_orcasighting" s
  JOIN "data_pipeline_zone" z
    ON z."zoneNumber" = s."zone"::int
  WHERE s."present" IS TRUE
    AND s."zone" ~ '^[0-9]+$'
  GROUP BY z."zoneNumber", EXTRACT(HOUR FROM s."time"), s."time"::date
),
agg2 AS (
  -- Average per day for that hour across all days in the dataset
  SELECT
    zone_id,
    hour,
    AVG(sightings)::float AS avg_sightings
  FROM hourly_daily
  GROUP BY zone_id, hour
)
INSERT INTO "data_pipeline_zoneeffort" ("zone_id", "hour", "avg_sightings")
SELECT zone_id, hour, avg_sightings
FROM agg2
ORDER BY zone_id, hour;

COMMIT;