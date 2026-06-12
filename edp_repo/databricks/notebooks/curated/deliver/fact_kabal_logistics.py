# databricks/notebooks/curated/deliver/fact_kabal_logistics.py
#
# Curated notebook — deliver.fact_kabal_logistics
# Security pattern: Asset filter (fn_asset_filter on asset_id)
# Source: euh_KBL (Kabal API)
# Domain: deliver
#
# This notebook validates the asset filter pattern before ADC go-live (Jan 2027).
# ADC models will follow the same pattern with euh_AIF as the source.
#
# Row filter binding:
#   - Applied on first run by calling infra/apply_row_filter
#   - Registry entry in unity_catalog/terraform/table_bindings.yaml
#   - Mapping data in prod_catalog.config.asset_group_map (seeded by migration scripts)

import logging
from pyspark.sql import functions as F

# ── Block 1: Widgets and config ───────────────────────────────────────────────

dbutils.widgets.text("catalog",      "",      "Target catalog")
dbutils.widgets.text("euh_schema",   "",      "EUH schema (e.g. euh_KBL or euh_prod_mirror_KBL)")
dbutils.widgets.text("domain_schema","",      "Curated domain schema (deliver)")
dbutils.widgets.text("load_type",    "delta", "full | delta")

catalog       = dbutils.widgets.get("catalog")
euh_schema    = dbutils.widgets.get("euh_schema")
domain_schema = dbutils.widgets.get("domain_schema")
load_type     = dbutils.widgets.get("load_type")

TABLE_NAME = "fact_kabal_logistics"
FULL_TABLE = f"{catalog}.{domain_schema}.{TABLE_NAME}"

assert catalog,       "catalog widget is required"
assert euh_schema,    "euh_schema widget is required"
assert domain_schema, "domain_schema widget is required"

# ── Block 2: Logging ──────────────────────────────────────────────────────────

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(f"edp.curated.deliver.{TABLE_NAME}")

run_id = dbutils.notebook.entry_point.getDbutils().notebook().getContext().currentRunId().toString()
logger.info(f"NOTEBOOK_START | table={FULL_TABLE} | load_type={load_type} | run_id={run_id}")

# ── Block 3: Transform and write ──────────────────────────────────────────────

try:
    # ── Read EUH ─────────────────────────────────────────────────────────────

    logger.info(f"READ_EUH | schema={catalog}.{euh_schema}")

    kabal_movements = spark.table(f"{catalog}.{euh_schema}.kabal_asset_movements")
    kabal_assets    = spark.table(f"{catalog}.{euh_schema}.kabal_assets")

    # ── Transform ─────────────────────────────────────────────────────────────
    # asset_id MUST be present — it is the row filter column for asset security.
    # fn_asset_filter checks the user's Entra group membership against asset_group_map
    # at query time — only rows for assets the user is permitted to see are returned.

    fact_kabal_logistics = (
        kabal_movements
        .join(kabal_assets, "asset_id", "inner")
        .select(
            F.col("movement_id"),
            F.col("asset_id"),               # ← row filter column — never drop
            F.col("asset_name"),
            F.col("movement_type"),
            F.col("origin_location"),
            F.col("destination_location"),
            F.col("planned_departure_dt"),
            F.col("actual_departure_dt"),
            F.col("planned_arrival_dt"),
            F.col("actual_arrival_dt"),
            F.col("cargo_weight_kg"),
            F.col("cargo_volume_m3"),
            F.when(
                F.col("actual_arrival_dt") <= F.col("planned_arrival_dt"), 1
            ).otherwise(0).alias("is_on_time"),
            F.lit("KBL").alias("source_id"),
        )
        .filter(F.col("asset_id").isNotNull())
    )

    row_count = fact_kabal_logistics.count()
    logger.info(f"TRANSFORM_COMPLETE | rows={row_count}")

    # ── Write ─────────────────────────────────────────────────────────────────

    table_exists = spark.catalog.tableExists(FULL_TABLE)
    first_run    = not table_exists

    if load_type == "full" or not table_exists:
        logger.info(f"WRITE_FULL | target={FULL_TABLE}")
        (
            fact_kabal_logistics.write
            .format("delta")
            .format("delta")
            .mode("overwrite")
            .option("overwriteSchema", "true")
            .saveAsTable(FULL_TABLE)
        )
    else:
        logger.info(f"WRITE_DELTA_MERGE | target={FULL_TABLE}")
        staging_view = f"fact_kabal_staging_{run_id}"
        fact_kabal_logistics.createOrReplaceTempView(staging_view)

        spark.sql(f"""
            MERGE INTO {FULL_TABLE} t
            USING {staging_view} s
            ON t.movement_id = s.movement_id
            WHEN MATCHED THEN UPDATE SET *
            WHEN NOT MATCHED THEN INSERT *
        """)

    logger.info(f"WRITE_COMPLETE | rows_written={row_count}")

    # ── Apply row filter on first run ─────────────────────────────────────────
    # apply_row_filter checks table_bindings.yaml — exits cleanly if this table is not registered.

    if first_run:
        logger.info(f"APPLY_ROW_FILTER | first_run=true | table={FULL_TABLE}")
        dbutils.notebook.run(
            "../../infra/apply_row_filter",
            timeout_seconds=120,
            arguments={
                "catalog":     catalog,
                "schema_name": domain_schema,
                "table_name":  TABLE_NAME,
            }
        )
        logger.info(f"APPLY_ROW_FILTER COMPLETE")

    # ── Log ───────────────────────────────────────────────────────────────────

    spark.sql(f"""
        INSERT INTO {catalog}.platform_config.pipeline_run_log VALUES (
            '{run_id}', '{FULL_TABLE}', '{load_type}', {row_count},
            'success', null, current_timestamp()
        )
    """)

    logger.info(f"NOTEBOOK_COMPLETE | table={FULL_TABLE} | rows={row_count}")
    dbutils.notebook.exit("SUCCESS")

except Exception as e:
    logger.error(f"NOTEBOOK_FAILED | table={FULL_TABLE} | error={e}")
    spark.sql(f"""
        INSERT INTO {catalog}.platform_config.pipeline_run_log VALUES (
            '{run_id}', '{FULL_TABLE}', '{load_type}', 0,
            'failed', '{str(e).replace("'","''")}', current_timestamp()
        )
    """)
    raise
