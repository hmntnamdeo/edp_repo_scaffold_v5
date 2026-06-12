-- databricks/migrations/platform/0004_create_legal_entity_asset_group_maps.sql
-- Creates the legal entity and asset group mapping tables.
-- Same pattern as lob_group_map — queried at runtime by their respective filter functions.

-- Legal entity map: used by fn_legal_entity_filter (Ariba/CLM models)
CREATE TABLE IF NOT EXISTS ${catalog}.config.legal_entity_group_map (
    company_code    STRING      NOT NULL,   -- e.g. "GB01", "DE02"
    entity_name     STRING      NOT NULL,   -- display name
    entra_group_id  STRING      NOT NULL,
    scope           STRING      NOT NULL,   -- 'ENTITY' | 'GLOBAL'
    is_active       BOOLEAN     NOT NULL    DEFAULT true,
    created_at      TIMESTAMP               DEFAULT current_timestamp(),
    updated_at      TIMESTAMP               DEFAULT current_timestamp(),
    updated_by      STRING
)
USING DELTA
LOCATION '${adls_path}/config/legal_entity_group_map';

-- Asset map: used by fn_asset_filter (Kabal + ADC models)
CREATE TABLE IF NOT EXISTS ${catalog}.config.asset_group_map (
    asset_id        STRING      NOT NULL,
    asset_name      STRING      NOT NULL,
    entra_group_id  STRING      NOT NULL,
    scope           STRING      NOT NULL,   -- 'ASSET' | 'GLOBAL'
    is_active       BOOLEAN     NOT NULL    DEFAULT true,
    created_at      TIMESTAMP               DEFAULT current_timestamp(),
    updated_at      TIMESTAMP               DEFAULT current_timestamp(),
    updated_by      STRING
)
USING DELTA
LOCATION '${adls_path}/config/asset_group_map';
