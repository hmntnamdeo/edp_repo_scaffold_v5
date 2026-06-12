# EDP platform — Copilot naming conventions

Read docs/naming_conventions.md for the full reference.
This file is a condensed version for Copilot suggestions.

## Layer names — always use, never Bronze/Silver/Gold
- Landing   (raw from source, no transformation)
- EUH       (EDAM-renamed, per source, no harmonised layer)
- Curated   (harmonised by supply chain domain)

## Schema patterns
Dev Landing:    landing_[SRC]_[ENV]          e.g. landing_BLP_A59
Dev EUH:        euh_[SRC]_[ENV]              e.g. euh_BLP_A59
Dev Curated:    feat_[FEATURE]_[DOMAIN]      e.g. feat_spend_v2_sourcing
UAT EUH:        euh_prod_mirror_[SRC]        e.g. euh_prod_mirror_BLP
UAT Curated:    stable_[DOMAIN]              e.g. stable_sourcing
Prod Landing:   landing_[SRC]               e.g. landing_BLP
Prod EUH:       euh_[SRC]                   e.g. euh_BLP
Prod Curated:   [DOMAIN]                    e.g. sourcing

## Six curated domains only
plan · sourcing · deliver · master · config · mapping

## Source IDs — short codes from config/source_systems.yml
BLP · ADC · CLM · FIN · KBL · AIF · ARB

## Notebook widget pattern — always use, never hardcode
catalog       = dbutils.widgets.get("catalog")
euh_schema    = dbutils.widgets.get("euh_schema")
domain_schema = dbutils.widgets.get("domain_schema")
load_type     = dbutils.widgets.get("load_type")

## Never suggest
- bronze / silver / gold in any name
- dev_[username] schemas — always use feat_[feature]_[domain]
- hardcoded catalog names or connection strings in notebooks
- DDL (ALTER TABLE, ADD COLUMN) inside notebooks — use migrations/ folder
- env ID in prod schema names — prod schemas have no env suffix
- euh_harmonised schema — this layer does not exist in this platform
- long source names (erp_sap, ariba) — always use short IDs (BLP, ARB)

## MSC Scala to PySpark — review these manually
- Window functions: always manually review converted output
- UDFs: verify execution semantics match original Scala behaviour
- Joins: confirm join type, broadcast hints, and null handling preserved
- Streaming vs batch: confirm execution model is appropriate

## Migration script pattern
-- Always idempotent
ALTER TABLE ${catalog}.sourcing.fact_spend
  ADD COLUMN IF NOT EXISTS new_col STRING;

UPDATE ${catalog}.sourcing.fact_spend
SET new_col = derived_value
WHERE new_col IS NULL;

## Delta MERGE pattern
MERGE INTO ${catalog}.${domain_schema}.${table} t
USING ${table}_staging s ON t.key_col = s.key_col
WHEN MATCHED THEN UPDATE SET *
WHEN NOT MATCHED THEN INSERT *
