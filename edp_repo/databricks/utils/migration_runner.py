# databricks/utils/migration_runner.py
#
# Applies pending migration scripts against a target catalog in sequence.
# Tracks applied migrations in platform_config.migration_history.
# Idempotent — skips already-applied migrations.
# Called by CI/CD deploy workflows before notebook deployment.
#
# Usage:
#   databricks runs submit --existing-cluster-id <id> \
#     --python-file dbfs:/utils/migration_runner.py \
#     --parameters catalog=prod_catalog env=prod

import glob
import os
import logging
from datetime import datetime

# ── Widgets ───────────────────────────────────────────────────────────────────

dbutils.widgets.text("catalog", "", "Target catalog")
dbutils.widgets.text("env",     "", "Environment: dev | uat | prod")

catalog = dbutils.widgets.get("catalog")
env     = dbutils.widgets.get("env")

assert catalog, "catalog widget is required"
assert env,     "env widget is required"

# ── Logging ───────────────────────────────────────────────────────────────────

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("edp.infra.migration_runner")

logger.info(f"MIGRATION_RUNNER START | catalog={catalog} | env={env}")

# ── Ensure migration history table exists ─────────────────────────────────────

spark.sql(f"""
    CREATE TABLE IF NOT EXISTS {catalog}.platform_config.migration_history (
        migration_id  STRING    NOT NULL,
        filename      STRING    NOT NULL,
        applied_at    TIMESTAMP NOT NULL,
        environment   STRING    NOT NULL,
        status        STRING    NOT NULL,   -- success | failed
        error_message STRING
    )
    USING DELTA
""")

# ── Load already-applied migrations ──────────────────────────────────────────

applied = set(
    row.migration_id
    for row in spark.sql(f"""
        SELECT migration_id
        FROM {catalog}.platform_config.migration_history
        WHERE environment = '{env}' AND status = 'success'
    """).collect()
)

logger.info(f"MIGRATION_RUNNER | already applied: {len(applied)} migrations")

# ── Find and apply pending migrations ─────────────────────────────────────────

migration_dirs = [
    "databricks/migrations/platform",
    "databricks/migrations/euh",
    "databricks/migrations/curated",
]

migration_files = sorted([
    f for d in migration_dirs
    for f in glob.glob(f"/Workspace/Repos/edp-data-platform/{d}/*.sql")
    if not f.endswith("_rollback.sql")   # rollback scripts never auto-applied
])

logger.info(f"MIGRATION_RUNNER | found {len(migration_files)} migration files")

for filepath in migration_files:
    migration_id = os.path.basename(filepath)

    if migration_id in applied:
        logger.info(f"MIGRATION_RUNNER SKIP | {migration_id} already applied")
        continue

    logger.info(f"MIGRATION_RUNNER APPLY | {migration_id}")

    try:
        sql_content = open(filepath).read()

        # Substitute catalog and env parameters
        sql_content = sql_content.replace("${catalog}", catalog)
        sql_content = sql_content.replace("${env}", env)

        # Execute each statement separated by semicolon
        for stmt in sql_content.split(";"):
            stmt = stmt.strip()
            if stmt and not stmt.startswith("--"):
                spark.sql(stmt)

        # Record success
        spark.sql(f"""
            INSERT INTO {catalog}.platform_config.migration_history
            VALUES (
                '{migration_id}',
                '{filepath}',
                current_timestamp(),
                '{env}',
                'success',
                null
            )
        """)

        logger.info(f"MIGRATION_RUNNER SUCCESS | {migration_id}")

    except Exception as e:
        error_msg = str(e).replace("'", "''")
        spark.sql(f"""
            INSERT INTO {catalog}.platform_config.migration_history
            VALUES (
                '{migration_id}',
                '{filepath}',
                current_timestamp(),
                '{env}',
                'failed',
                '{error_msg}'
            )
        """)
        logger.error(f"MIGRATION_RUNNER FAILED | {migration_id} | {e}")
        raise

logger.info(f"MIGRATION_RUNNER COMPLETE | catalog={catalog} | env={env}")
