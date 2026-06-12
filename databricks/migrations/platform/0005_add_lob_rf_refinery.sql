-- databricks/migrations/platform/0005_add_lob_rf_refinery.sql
-- Example: Adding a new LOB group — Refinery (RF)
-- This goes through normal PR + CI + release manager gate.
-- Never INSERT directly into prod — always via migration runner.
--
-- Paired rollback: 0005_add_lob_rf_refinery_rollback.sql

INSERT INTO ${catalog}.config.lob_group_map
    (lob_code, lob_name, entra_group_id, scope, is_active, updated_by)
VALUES
    ('RF', 'Refinery', '<entra-group-id-refinery>', 'LOB', true, 'migration-0005');
