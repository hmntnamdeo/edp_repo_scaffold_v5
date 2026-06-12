-- databricks/migrations/platform/0001_create_orchestration_config.sql
-- Creates the orchestration config table.
-- Run once at platform initialisation via migration_runner.py.
-- Idempotent: CREATE TABLE IF NOT EXISTS

CREATE TABLE IF NOT EXISTS ${catalog}.config.orchestration_config (
    table_id            STRING      NOT NULL,   -- e.g. "sourcing.fact_spend"
    catalog_name        STRING      NOT NULL,
    schema_name         STRING      NOT NULL,
    table_name          STRING      NOT NULL,
    load_type           STRING      NOT NULL,   -- "full" | "delta"
    is_active           BOOLEAN     NOT NULL,
    dependency_tables   ARRAY<STRING>,
    watermark_column    STRING,
    watermark_value     STRING,
    run_order           INT         NOT NULL,
    first_load_complete BOOLEAN     NOT NULL    DEFAULT false,
    feature_flag        STRING,                 -- links row to the feature that introduced it
    notes               STRING,
    created_at          TIMESTAMP               DEFAULT current_timestamp(),
    updated_at          TIMESTAMP               DEFAULT current_timestamp()
)
USING DELTA
LOCATION '${adls_path}/config/orchestration_config';
