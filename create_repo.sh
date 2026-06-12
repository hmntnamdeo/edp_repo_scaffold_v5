#!/bin/bash
# EDP Data Platform — GitHub repository scaffold
# Run this script from inside your cloned empty repo
# Usage: bash create_repo.sh

set -e

echo "Creating EDP Data Platform repository structure..."

# ── .github ──────────────────────────────────────────────
mkdir -p .github/workflows
mkdir -p .github/copilot/prompts
mkdir -p .github/ISSUE_TEMPLATE

touch .github/workflows/ci.yml
touch .github/workflows/deploy-dev.yml
touch .github/workflows/deploy-uat.yml
touch .github/workflows/deploy-prod.yml
touch .github/workflows/nightly-sync.yml
touch .github/workflows/rollback.yml
touch .github/CODEOWNERS
touch .github/pull_request_template.md
touch .github/copilot/instructions.md
touch .github/copilot/prompts/euh-transform.md
touch .github/copilot/prompts/curated-merge.md
touch .github/copilot/prompts/scala-to-pyspark.md

# ── adf ──────────────────────────────────────────────────
mkdir -p adf/pipeline/landing
mkdir -p adf/pipeline/copy
mkdir -p adf/linkedService
mkdir -p adf/dataset
mkdir -p adf/trigger

touch adf/pipeline/landing/.gitkeep
touch adf/pipeline/copy/.gitkeep
touch adf/linkedService/.gitkeep
touch adf/dataset/.gitkeep
touch adf/trigger/.gitkeep

# ── databricks ───────────────────────────────────────────
mkdir -p databricks/bundle
mkdir -p databricks/notebooks/landing/BLP
mkdir -p databricks/notebooks/landing/ARB
mkdir -p databricks/notebooks/landing/CLM
mkdir -p databricks/notebooks/landing/KBL
mkdir -p databricks/notebooks/landing/FIN
mkdir -p databricks/notebooks/landing/AIF
mkdir -p databricks/notebooks/euh/BLP
mkdir -p databricks/notebooks/euh/ARB
mkdir -p databricks/notebooks/euh/CLM
mkdir -p databricks/notebooks/euh/KBL
mkdir -p databricks/notebooks/euh/FIN
mkdir -p databricks/notebooks/euh/AIF
mkdir -p databricks/notebooks/curated/plan
mkdir -p databricks/notebooks/curated/sourcing
mkdir -p databricks/notebooks/curated/deliver
mkdir -p databricks/notebooks/curated/master
mkdir -p databricks/notebooks/curated/msc
mkdir -p databricks/notebooks/curated/mapping
mkdir -p databricks/migrations/platform
mkdir -p databricks/migrations/euh
mkdir -p databricks/migrations/curated
mkdir -p databricks/utils

touch databricks/bundle/databricks.yml
touch databricks/notebooks/landing/BLP/.gitkeep
touch databricks/notebooks/landing/ARB/.gitkeep
touch databricks/notebooks/landing/CLM/.gitkeep
touch databricks/notebooks/landing/KBL/.gitkeep
touch databricks/notebooks/landing/FIN/.gitkeep
touch databricks/notebooks/landing/AIF/.gitkeep
touch databricks/notebooks/euh/BLP/.gitkeep
touch databricks/notebooks/euh/ARB/.gitkeep
touch databricks/notebooks/euh/CLM/.gitkeep
touch databricks/notebooks/euh/KBL/.gitkeep
touch databricks/notebooks/euh/FIN/.gitkeep
touch databricks/notebooks/euh/AIF/.gitkeep
touch databricks/notebooks/curated/plan/.gitkeep
touch databricks/notebooks/curated/sourcing/.gitkeep
touch databricks/notebooks/curated/deliver/.gitkeep
touch databricks/notebooks/curated/master/.gitkeep
touch databricks/notebooks/curated/msc/.gitkeep
touch databricks/notebooks/curated/mapping/.gitkeep
touch databricks/migrations/platform/.gitkeep
touch databricks/migrations/euh/.gitkeep
touch databricks/migrations/curated/.gitkeep
touch databricks/utils/migration_runner.py
touch databricks/utils/orchestration_runner.py
touch databricks/utils/schema_drift_check.py
touch databricks/utils/uat_provision_schema.py

# ── unity_catalog ─────────────────────────────────────────
mkdir -p unity_catalog/terraform/envs
mkdir -p unity_catalog/scripts

touch unity_catalog/terraform/catalogs.tf
touch unity_catalog/terraform/schemas.tf
touch unity_catalog/terraform/grants.tf
touch unity_catalog/terraform/row_filters.tf
touch unity_catalog/terraform/table_bindings.yaml
touch unity_catalog/terraform/envs/dev.tfvars
touch unity_catalog/terraform/envs/uat.tfvars
touch unity_catalog/terraform/envs/prod.tfvars
touch unity_catalog/scripts/schema_diff.py

# ── powerbi ───────────────────────────────────────────────
mkdir -p powerbi/semantic_models/plan
mkdir -p powerbi/semantic_models/sourcing
mkdir -p powerbi/semantic_models/deliver
mkdir -p powerbi/semantic_models/master
mkdir -p powerbi/semantic_models/mapping
mkdir -p powerbi/reports/msc
mkdir -p powerbi/reports/adc

touch powerbi/semantic_models/plan/.gitkeep
touch powerbi/semantic_models/sourcing/.gitkeep
touch powerbi/semantic_models/deliver/.gitkeep
touch powerbi/semantic_models/master/.gitkeep
touch powerbi/semantic_models/mapping/.gitkeep
touch powerbi/reports/msc/.gitkeep
touch powerbi/reports/adc/.gitkeep

# ── mapping_files ─────────────────────────────────────────
mkdir -p mapping_files/streamlit_app
mkdir -p mapping_files/schemas

touch mapping_files/streamlit_app/app.py
touch mapping_files/streamlit_app/validation.py
touch mapping_files/streamlit_app/approval_workflow.py
touch mapping_files/schemas/.gitkeep

# ── infrastructure ────────────────────────────────────────
mkdir -p infrastructure/bicep
mkdir -p infrastructure/scripts

touch infrastructure/bicep/adls.bicep
touch infrastructure/bicep/databricks.bicep
touch infrastructure/bicep/keyvault.bicep
touch infrastructure/scripts/.gitkeep

# ── config ────────────────────────────────────────────────
mkdir -p config

touch config/dev.yml
touch config/uat.yml
touch config/prod.yml
touch config/source_systems.yml
touch config/uat_clone_scope.yml

# ── tests ─────────────────────────────────────────────────
mkdir -p tests/unit
mkdir -p tests/integration
mkdir -p tests/great_expectations/suites

touch tests/unit/.gitkeep
touch tests/integration/.gitkeep
touch tests/great_expectations/suites/curated_sourcing.json
touch tests/great_expectations/suites/curated_deliver.json
touch tests/great_expectations/suites/curated_plan.json
touch tests/great_expectations/suites/curated_master.json
touch tests/great_expectations/suites/curated_mapping.json
touch tests/great_expectations/suites/euh_BLP.json
touch tests/great_expectations/suites/euh_ARB.json

# ── docs ──────────────────────────────────────────────────
mkdir -p docs/adr

touch docs/naming_conventions.md
touch docs/ways_of_working.md
touch docs/runbook.md
touch docs/adr/.gitkeep

# ── root ──────────────────────────────────────────────────
touch README.md
touch .gitignore

echo ""
echo "Structure created. Files to populate before first commit:"
echo "  1. README.md"
echo "  2. .github/CODEOWNERS"
echo "  3. .github/copilot/instructions.md"
echo "  4. config/source_systems.yml"
echo "  5. config/dev.yml / uat.yml / prod.yml"
echo "  6. config/uat_clone_scope.yml"
echo "  7. databricks/bundle/databricks.yml"
echo "  8. docs/naming_conventions.md"
echo "  9. .github/workflows/ci.yml"
echo " 10. unity_catalog/terraform/grants.tf"
echo ""
echo "Done. Run: git add . && git commit -m 'chore: scaffold repo structure'"
