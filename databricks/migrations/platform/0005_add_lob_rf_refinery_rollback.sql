-- databricks/migrations/platform/0005_add_lob_rf_refinery_rollback.sql
-- Rollback for 0005_add_lob_rf_refinery.sql
-- Soft delete — never hard DELETE for audit continuity

UPDATE ${catalog}.config.lob_group_map
SET    is_active  = false,
       updated_at = current_timestamp(),
       updated_by = 'rollback-0005'
WHERE  lob_code = 'RF';
