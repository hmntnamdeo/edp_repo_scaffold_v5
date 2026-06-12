# databricks/notebooks/curated/sourcing/fact_spend.py
#
# Curated notebook — sourcing.fact_spend
# Security pattern: Legal entity filter (fn_legal_entity_filter on company_code)
# Source: euh_ARB (Ariba) + euh_CLM (CLM) via EUH schemas
# Domain: sourcing
#
# Row filter binding:
#   - Applied on first run by calling infra/apply_row_filter
#   - Registry entry in unity_catalog/terraform/table_bindings.yaml
#   - Filter function deployed by Terraform in row_filters.tf
#   - Mapping data in prod_catalog.config.legal_entity_group_map (seeded by migration scripts)

import logging
from pyspark.sql import functions as F
from delta.tables import DeltaTable

# ── Block 1: Widgets and config ───────────────────────────────────────────────

dbutils.widgets.text("catalog",      "",      "Target catalog")
dbutils.widgets.text("euh_schema_arb", "",    "Ariba EUH schema")
dbutils.widgets.text("euh_schema_clm", "",    "CLM EUH schema")
dbutils.widgets.text("domain_schema",  "",    "Curated domain schema (sourcing)")
dbutils.widgets.text("load_type",    "delta", "full | delta")

catalog         = dbutils.widgets.get("catalog")
euh_schema_arb  = dbutils.widgets.get("euh_schema_arb")
euh_schema_clm  = dbutils.widgets.get("euh_schema_clm")
domain_schema   = dbutils.widgets.get("domain_schema")
load_type       = dbutils.widgets.get("load_type")

TABLE_NAME = "fact_spend"
FULL_TABLE = f"{catalog}.{domain_schema}.{TABLE_NAME}"

assert catalog,        "catalog widget is required"
assert euh_schema_arb, "euh_schema_arb widget is required"
assert domain_schema,  "domain_schema widget is required"

# ── Block 2: Logging setup ────────────────────────────────────────────────────

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(f"edp.curated.sourcing.{TABLE_NAME}")

run_id = dbutils.notebook.entry_point.getDbutils().notebook().getContext().currentRunId().toString()
logger.info(f"NOTEBOOK_START | table={FULL_TABLE} | load_type={load_type} | run_id={run_id}")

# ── Block 3: Transform and write ──────────────────────────────────────────────

try:
    # ── Read from EUH ────────────────────────────────────────────────────────

    logger.info(f"READ_EUH | schema={catalog}.{euh_schema_arb}")

    arb_spend = spark.table(f"{catalog}.{euh_schema_arb}.arb_spend_lines")
    clm_contracts = spark.table(f"{catalog}.{euh_schema_clm}.clm_contract_lines") \
        if euh_schema_clm else None

    # ── Transform ─────────────────────────────────────────────────────────────
    # company_code MUST be present — it is the row filter column for legal entity security.
    # Any row without company_code will be invisible to all end users after the filter is applied.

    fact_spend = (
        arb_spend
        .select(
            F.col("EBELN").alias("po_number"),
            F.col("EBELP").alias("po_line_number"),
            F.col("BUKRS").alias("company_code"),   # ← row filter column — never drop
            F.col("LIFNR").alias("vendor_id"),
            F.col("MATNR").alias("material_id"),
            F.col("MENGE").alias("quantity"),
            F.col("NETWR").alias("net_value"),
            F.col("WAERS").alias("currency"),
            F.col("BEDAT").alias("po_date"),
            F.col("ERDAT").alias("created_date"),
            F.lit("ARB").alias("source_id"),
        )
        .filter(F.col("company_code").isNotNull())  # safety: filter rows with no company_code
    )

    # Join CLM contract data if available
    if clm_contracts:
        fact_spend = fact_spend.join(
            clm_contracts.select("po_number", "contract_id", "contract_type"),
            on="po_number",
            how="left"
        )
    else:
        fact_spend = fact_spend.withColumn("contract_id", F.lit(None).cast("string")) \
                               .withColumn("contract_type", F.lit(None).cast("string"))

    row_count = fact_spend.count()
    logger.info(f"TRANSFORM_COMPLETE | rows={row_count}")

    # ── Write: full or delta ──────────────────────────────────────────────────

    table_exists = spark.catalog.tableExists(FULL_TABLE)
    first_run    = not table_exists

    if load_type == "full" or not table_exists:
        logger.info(f"WRITE_FULL | target={FULL_TABLE}")
        (
            fact_spend.write
            .format("delta")
            .mode("overwrite")
            .option("overwriteSchema", "true")
            .saveAsTable(FULL_TABLE)
        )
    else:
        logger.info(f"WRITE_DELTA_MERGE | target={FULL_TABLE}")
        staging_view = f"fact_spend_staging_{run_id}"
        fact_spend.createOrReplaceTempView(staging_view)

        spark.sql(f"""
            MERGE INTO {FULL_TABLE} t
            USING {staging_view} s
            ON t.po_number = s.po_number AND t.po_line_number = s.po_line_number
            WHEN MATCHED THEN UPDATE SET *
            WHEN NOT MATCHED THEN INSERT *
        """)

    logger.info(f"WRITE_COMPLETE | rows_written={row_count}")

    # ── Apply row filter on first run ─────────────────────────────────────────
    # apply_row_filter checks table_bindings.yaml — exits cleanly if this table is not registered.
    # Table now exists in UC — safe to apply the binding.

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
            '{run_id}',
            '{FULL_TABLE}',
            '{load_type}',
            {row_count},
            'success',
            null,
            current_timestamp()
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
