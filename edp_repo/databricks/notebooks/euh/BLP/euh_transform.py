# databricks/notebooks/euh/BLP/euh_transform.py
#
# EUH transformation notebook — BLP source (SAP ERP)
# Reads from landing_BLP and writes to euh_BLP schema.
# Applies EDAM field renaming — source field names → standard EDAM names.
# No business logic here — that belongs in curated notebooks.
#
# This notebook does NOT apply row filters — EUH layer access is controlled by:
#   - MSVC: schema-level SELECT GRANT to MSVC-Approved group (grants.tf)
#   - All other consumers: read via curated notebooks only (curated has row filters)

import logging
from pyspark.sql import functions as F

# ── Block 1: Widgets ──────────────────────────────────────────────────────────

dbutils.widgets.text("catalog",        "", "Target catalog")
dbutils.widgets.text("landing_schema", "", "Landing schema (e.g. landing_BLP_A59)")
dbutils.widgets.text("euh_schema",     "", "EUH schema (e.g. euh_BLP_A59)")
dbutils.widgets.text("load_type",      "delta", "full | delta")
dbutils.widgets.text("watermark_value","", "Watermark for delta load (ERDAT)")

catalog        = dbutils.widgets.get("catalog")
landing_schema = dbutils.widgets.get("landing_schema")
euh_schema     = dbutils.widgets.get("euh_schema")
load_type      = dbutils.widgets.get("load_type")
watermark_value= dbutils.widgets.get("watermark_value")

SOURCE_ID = "BLP"

assert catalog,        "catalog widget is required"
assert landing_schema, "landing_schema widget is required"
assert euh_schema,     "euh_schema widget is required"

# ── Block 2: Logging ──────────────────────────────────────────────────────────

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(f"edp.euh.{SOURCE_ID}")

run_id = dbutils.notebook.entry_point.getDbutils().notebook().getContext().currentRunId().toString()
logger.info(f"NOTEBOOK_START | source={SOURCE_ID} | load_type={load_type} | run_id={run_id}")

# ── Block 3: Transform tables ─────────────────────────────────────────────────

try:
    # Tables to process in this EUH run
    # Each tuple: (landing_table, euh_table, key_columns, watermark_column)
    tables = [
        ("ekko_raw", "ekko", ["EBELN"],          "AEDAT"),  # PO header
        ("ekpo_raw", "ekpo", ["EBELN", "EBELP"], "AEDAT"),  # PO items
        ("likp_raw", "likp", ["VBELN"],           "ERDAT"),  # delivery header
        ("lips_raw", "lips", ["VBELN", "POSNR"], "ERDAT"),  # delivery items
        ("vbak_raw", "vbak", ["VBELN"],           "ERDAT"),  # sales order header
        ("mara_raw", "mara", ["MATNR"],           "LAEDA"),  # material master
    ]

    total_rows = 0

    for landing_table, euh_table, key_cols, wm_col in tables:
        full_landing = f"{catalog}.{landing_schema}.{landing_table}"
        full_euh     = f"{catalog}.{euh_schema}.{euh_table}"

        logger.info(f"EUH_TABLE_START | {landing_table} -> {euh_table}")

        df = spark.table(full_landing)

        # Apply watermark filter for delta loads
        if load_type == "delta" and watermark_value:
            df = df.filter(F.col(wm_col) > watermark_value)
            logger.info(f"WATERMARK_FILTER | col={wm_col} | from={watermark_value}")

        # EDAM field renaming happens here
        # In production: apply full EDAM mapping from a lookup config
        # For this example: passthrough with _edam suffix tracking
        df = df.withColumn("_source_id",    F.lit(SOURCE_ID)) \
               .withColumn("_loaded_at",    F.current_timestamp()) \
               .withColumn("_load_type",    F.lit(load_type))

        row_count = df.count()
        total_rows += row_count

        table_exists = spark.catalog.tableExists(full_euh)

        if load_type == "full" or not table_exists:
            df.write.format("delta").mode("overwrite") \
              .option("overwriteSchema", "true").saveAsTable(full_euh)
        else:
            staging = f"{euh_table}_staging_{run_id}"
            df.createOrReplaceTempView(staging)
            key_condition = " AND ".join([f"t.{k} = s.{k}" for k in key_cols])
            spark.sql(f"""
                MERGE INTO {full_euh} t
                USING {staging} s ON {key_condition}
                WHEN MATCHED THEN UPDATE SET *
                WHEN NOT MATCHED THEN INSERT *
            """)

        logger.info(f"EUH_TABLE_COMPLETE | {euh_table} | rows={row_count}")

    # ── Log ───────────────────────────────────────────────────────────────────

    spark.sql(f"""
        INSERT INTO {catalog}.platform_config.pipeline_run_log VALUES (
            '{run_id}', '{catalog}.{euh_schema}', '{load_type}', {total_rows},
            'success', null, current_timestamp()
        )
    """)

    logger.info(f"NOTEBOOK_COMPLETE | source={SOURCE_ID} | total_rows={total_rows}")
    dbutils.notebook.exit("SUCCESS")

except Exception as e:
    logger.error(f"NOTEBOOK_FAILED | source={SOURCE_ID} | error={e}")
    spark.sql(f"""
        INSERT INTO {catalog}.platform_config.pipeline_run_log VALUES (
            '{run_id}', '{catalog}.{euh_schema}', '{load_type}', 0,
            'failed', '{str(e).replace("'","''")}', current_timestamp()
        )
    """)
    raise
