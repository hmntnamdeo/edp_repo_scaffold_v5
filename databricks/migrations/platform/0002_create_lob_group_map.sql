-- databricks/migrations/platform/0002_create_lob_group_map.sql
-- Creates the LOB to Entra group mapping table.
-- This table is queried at runtime by fn_lob_filter in Unity Catalog.
-- It must exist BEFORE the row filter functions are deployed by Terraform.
-- It must exist BEFORE any curated notebook runs that bind fn_lob_filter.
--
-- Managed via migration scripts — never edited manually in prod.
-- Changes (add LOB, deactivate group, change Entra ID) go through PR + migration runner.
-- Delta transaction log provides full audit trail of all changes.

CREATE TABLE IF NOT EXISTS ${catalog}.config.lob_group_map (
    lob_code        STRING      NOT NULL,   -- short code e.g. UP, DS, GF
    lob_name        STRING      NOT NULL,   -- display name e.g. Upstream
    entra_group_id  STRING      NOT NULL,   -- Entra group object ID
    scope           STRING      NOT NULL,   -- 'LOB' | 'GLOBAL'
                                            -- GLOBAL = access to all LOBs
    is_active       BOOLEAN     NOT NULL    DEFAULT true,
    created_at      TIMESTAMP               DEFAULT current_timestamp(),
    updated_at      TIMESTAMP               DEFAULT current_timestamp(),
    updated_by      STRING
)
USING DELTA
LOCATION '${adls_path}/config/lob_group_map';
