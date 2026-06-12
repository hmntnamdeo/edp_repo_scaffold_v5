# databricks/notebooks/infra/apply_row_filter.py
#
# Applies a row filter binding to a table on first run.
# Called by curated notebooks immediately after CREATE TABLE / first Delta write.
#
# Whether a table needs a row filter is determined entirely by whether it has
# an entry in unity_catalog/terraform/table_bindings.yaml.
# Table naming conventions (fact_/dim_) are NOT used to infer this — naming
# on this platform is inconsistent and the registry is the source of truth.
#
# Behaviour:
#   - Table IS in registry  → apply ALTER TABLE ... SET ROW FILTER
#   - Table NOT in registry → exit cleanly with SKIPPED (no filter needed)
#   - Table in registry but filter column missing → raise (data integrity error)
#
# Usage (called from any curated notebook after first write):
#   dbutils.notebook.run(
#       "../../infra/apply_row_filter",
#       timeout_seconds=120,
#       arguments={
#           "catalog":      catalog,
#           "schema_name":  domain_schema,
#           "table_name":   "dim_spend_category",   # works regardless of name prefix
#       }
#   )
#
# The binding is idempotent — re-running replaces the existing binding.

import yaml
import logging

# ── Widgets ───────────────────────────────────────────────────────────────────

dbutils.widgets.text("catalog",     "", "Catalog name")
dbutils.widgets.text("schema_name", "", "Schema name (e.g. sourcing)")
dbutils.widgets.text("table_name",  "", "Table name (e.g. dim_spend_category)")

catalog     = dbutils.widgets.get("catalog")
schema_name = dbutils.widgets.get("schema_name")
table_name  = dbutils.widgets.get("table_name")

assert catalog,     "catalog widget is required"
assert schema_name, "schema_name widget is required"
assert table_name,  "table_name widget is required"

# ── Logging ───────────────────────────────────────────────────────────────────

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("edp.infra.apply_row_filter")

logger.info(f"APPLY_ROW_FILTER START | table={catalog}.{schema_name}.{table_name}")

# ── Load binding registry ─────────────────────────────────────────────────────

BINDINGS_PATH = "/Workspace/Repos/edp-data-platform/unity_catalog/terraform/table_bindings.yaml"

with open(BINDINGS_PATH) as f:
    registry = yaml.safe_load(f)

registered = {
    (b["schema"], b["table"]): b
    for b in registry["table_bindings"]
    if b.get("row_filter") and b.get("row_filter") != "none"
}

# ── Look up binding for this table ────────────────────────────────────────────
# Not in registry = no row filter required for this table. Exit cleanly.

binding = registered.get((schema_name, table_name))

if not binding:
    logger.info(
        f"APPLY_ROW_FILTER SKIP | {schema_name}.{table_name} not in table_bindings.yaml "
        f"— no row filter applied. If this table needs one, add it to table_bindings.yaml."
    )
    dbutils.notebook.exit("SKIPPED")

row_filter_fn = binding["row_filter"]
filter_column = binding["filter_column"]

logger.info(f"APPLY_ROW_FILTER BINDING FOUND | filter={row_filter_fn} | column={filter_column}")

# ── Apply the row filter ──────────────────────────────────────────────────────
# Filter functions live in prod_catalog.config and are deployed by Terraform.
# Referenced by full path so they work regardless of which catalog the table is in.

filter_fn_ref = f"prod_catalog.config.{row_filter_fn}"

sql = f"""
    ALTER TABLE {catalog}.{schema_name}.{table_name}
    SET ROW FILTER {filter_fn_ref} ON ({filter_column})
"""

logger.info(f"APPLY_ROW_FILTER SQL | {sql.strip()}")

spark.sql(sql)

logger.info(
    f"APPLY_ROW_FILTER COMPLETE | table={catalog}.{schema_name}.{table_name} "
    f"| filter={row_filter_fn} | column={filter_column}"
)
