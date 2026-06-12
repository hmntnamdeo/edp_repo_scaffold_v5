# databricks/notebooks/curated/plan/fact_mot.py
#
# Curated notebook — plan.fact_mot (Material on Time)
# Security pattern: LOB filter (fn_lob_filter on lob_code)
# Source: euh_BLP (SAP ERP — MSC source)
# Domain: plan
#
# Row filter binding:
#   - Applied on first run by calling infra/apply_row_filter
#   - Registry entry in unity_catalog/terraform/table_bindings.yaml
#   - Mapping data in prod_catalog.config.lob_group_map
#     LOBs: UP (Upstream), DS (Downstream), GF (Functions), GLOBAL (All)

import logging
from pyspark.sql import functions as F

# ── Block 1: Widgets and config ───────────────────────────────────────────────

dbutils.widgets.text("catalog",      "",      "Target catalog")
dbutils.widgets.text("euh_schema",   "",      "EUH schema (e.g. euh_BLP or euh_prod_mirror_BLP)")
dbutils.widgets.text("domain_schema","",      "Curated domain schema (plan)")
dbutils.widgets.text("load_type",    "delta", "full | delta")

catalog       = dbutils.widgets.get("catalog")
euh_schema    = dbutils.widgets.get("euh_schema")
domain_schema = dbutils.widgets.get("domain_schema")
load_type     = dbutils.widgets.get("load_type")

TABLE_NAME = "fact_mot"
FULL_TABLE = f"{catalog}.{domain_schema}.{TABLE_NAME}"

assert catalog,       "catalog widget is required"
assert euh_schema,    "euh_schema widget is required"
assert domain_schema, "domain_schema widget is required"

# ── Block 2: Logging setup ────────────────────────────────────────────────────

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(f"edp.curated.plan.{TABLE_NAME}")

run_id = dbutils.notebook.entry_point.getDbutils().notebook().getContext().currentRunId().toString()
logger.info(f"NOTEBOOK_START | table={FULL_TABLE} | load_type={load_type} | run_id={run_id}")

# ── Block 3: Transform and write ──────────────────────────────────────────────

try:
    # ── Read EUH ─────────────────────────────────────────────────────────────

    logger.info(f"READ_EUH | schema={catalog}.{euh_schema}")

    deliveries  = spark.table(f"{catalog}.{euh_schema}.likp")   # delivery header
    delivery_items = spark.table(f"{catalog}.{euh_schema}.lips") # delivery items
    orders      = spark.table(f"{catalog}.{euh_schema}.vbak")   # sales order header
    materials   = spark.table(f"{catalog}.{euh_schema}.mara")   # material master

    # ── Transform ─────────────────────────────────────────────────────────────
    # lob_code MUST be present — it is the row filter column for LOB security.
    # LOB derivation: mapped from plant/division in EUH → lob_group_map at query time.
    # The notebook derives lob_code from source attributes — it does NOT read lob_group_map.
    # fn_lob_filter reads lob_group_map at query time to check Entra group membership.

    fact_mot = (
        deliveries
        .join(delivery_items, "VBELN", "inner")
        .join(orders, deliveries.VGBEL == orders.VBELN, "left")
        .join(materials, delivery_items.MATNR == materials.MATNR, "left")
        .select(
            delivery_items.VBELN.alias("delivery_number"),
            delivery_items.POSNR.alias("delivery_item"),
            orders.VBELN.alias("order_number"),
            delivery_items.MATNR.alias("material_number"),
            delivery_items.LFIMG.alias("delivered_quantity"),
            delivery_items.VRKME.alias("unit_of_measure"),
            deliveries.WADAT_IST.alias("actual_goods_issue_date"),
            orders.VDATU.alias("requested_delivery_date"),
            # lob_code derived from division — maps to UP/DS/GF in lob_group_map
            F.when(materials.SPART == "01", "UP")
             .when(materials.SPART == "02", "DS")
             .when(materials.SPART == "03", "GF")
             .otherwise("UNKNOWN")
             .alias("lob_code"),                              # ← row filter column — never drop
            # on_time flag: 1 if delivered on or before requested date
            F.when(
                deliveries.WADAT_IST <= orders.VDATU, 1
            ).otherwise(0).alias("is_on_time"),
            F.lit("BLP").alias("source_id"),
        )
        .filter(F.col("lob_code") != "UNKNOWN")  # rows without LOB are excluded
    )

    row_count = fact_mot.count()
    logger.info(f"TRANSFORM_COMPLETE | rows={row_count}")

    # ── Write ─────────────────────────────────────────────────────────────────

    table_exists = spark.catalog.tableExists(FULL_TABLE)
    first_run    = not table_exists

    if load_type == "full" or not table_exists:
        logger.info(f"WRITE_FULL | target={FULL_TABLE}")
        (
            fact_mot.write
            .format("delta")
            .mode("overwrite")
            .option("overwriteSchema", "true")
            .saveAsTable(FULL_TABLE)
        )
    else:
        logger.info(f"WRITE_DELTA_MERGE | target={FULL_TABLE}")
        staging_view = f"fact_mot_staging_{run_id}"
        fact_mot.createOrReplaceTempView(staging_view)

        spark.sql(f"""
            MERGE INTO {FULL_TABLE} t
            USING {staging_view} s
            ON  t.delivery_number = s.delivery_number
            AND t.delivery_item   = s.delivery_item
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

    # ── Log to pipeline_run_log ───────────────────────────────────────────────

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
