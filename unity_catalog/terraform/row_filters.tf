# unity_catalog/terraform/row_filters.tf
# Deploys the four row filter FUNCTIONS to Unity Catalog.
#
# IMPORTANT — what this file does and does not do:
#   ✓ Creates the SQL filter functions in prod_catalog.config
#   ✓ Creates the column masking function for UAT developer access
#   ✗ Does NOT bind filters to tables (tables are created on the fly by notebooks)
#
# Filter binding happens in two places:
#   1. Notebooks apply ALTER TABLE ... SET ROW FILTER on first run
#      (see databricks/notebooks/infra/apply_row_filter.py)
#   2. Migration scripts rebind filters when security changes post-deploy
#      (see databricks/migrations/platform/)
#
# The mapping data (which Entra group maps to which LOB/entity/asset) lives in:
#   prod_catalog.config.lob_group_map
#   prod_catalog.config.legal_entity_group_map
#   prod_catalog.config.asset_group_map
# These tables are seeded by migration scripts, not by Terraform.
# The functions below JOIN against these tables at query time.
# Entra ID is always the source of truth — no data is replicated out of Entra.

# ── Pattern 1: LOB filter ─────────────────────────────────────────────────────
# Used by: plan domain (MSC/MOT), deliver domain (RTP), most sourcing models
# Columns filtered: lob_code
# Entra claim: group membership checked against lob_group_map at query time

resource "databricks_sql_function" "fn_lob_filter" {
  catalog_name = var.catalog_name   # prod_catalog in prod; applied per env via tfvars
  schema_name  = "config"
  name         = "fn_lob_filter"
  comment      = "LOB row filter — checks user Entra group membership against config.lob_group_map"

  input_params {
    parameters {
      name      = "lob_code"
      type_text = "STRING"
    }
  }

  return_type {
    type_text = "BOOLEAN"
  }

  # Function returns TRUE (row visible) if:
  #   a) user is a member of the Entra group mapped to this lob_code, OR
  #   b) user is a member of a GLOBAL scope group (access to all LOBs)
  body = <<-SQL
    EXISTS (
      SELECT 1
      FROM ${var.catalog_name}.config.lob_group_map m
      WHERE m.lob_code = lob_code
        AND m.is_active = true
        AND is_account_group_member(m.entra_group_id)
    )
    OR
    EXISTS (
      SELECT 1
      FROM ${var.catalog_name}.config.lob_group_map m
      WHERE m.scope = 'GLOBAL'
        AND m.is_active = true
        AND is_account_group_member(m.entra_group_id)
    )
  SQL
}

# ── Pattern 2: Legal entity filter ───────────────────────────────────────────
# Used by: sourcing domain — Ariba/CLM models (fact_spend, fact_contracts)
# Columns filtered: company_code
# Entra claim: group membership checked against legal_entity_group_map

resource "databricks_sql_function" "fn_legal_entity_filter" {
  catalog_name = var.catalog_name
  schema_name  = "config"
  name         = "fn_legal_entity_filter"
  comment      = "Legal entity row filter — checks user Entra group against config.legal_entity_group_map"

  input_params {
    parameters {
      name      = "company_code"
      type_text = "STRING"
    }
  }

  return_type {
    type_text = "BOOLEAN"
  }

  body = <<-SQL
    EXISTS (
      SELECT 1
      FROM ${var.catalog_name}.config.legal_entity_group_map m
      WHERE m.company_code = company_code
        AND m.is_active = true
        AND is_account_group_member(m.entra_group_id)
    )
    OR
    EXISTS (
      SELECT 1
      FROM ${var.catalog_name}.config.legal_entity_group_map m
      WHERE m.scope = 'GLOBAL'
        AND m.is_active = true
        AND is_account_group_member(m.entra_group_id)
    )
  SQL
}

# ── Pattern 3: Asset filter ───────────────────────────────────────────────────
# Used by: deliver domain — Kabal models, ADC models
# Columns filtered: asset_id
# Entra claim: group membership checked against asset_group_map
# Note: validates the ADC asset security pattern before ADC go-live (Jan 2027)

resource "databricks_sql_function" "fn_asset_filter" {
  catalog_name = var.catalog_name
  schema_name  = "config"
  name         = "fn_asset_filter"
  comment      = "Asset row filter — checks user Entra group against config.asset_group_map"

  input_params {
    parameters {
      name      = "asset_id"
      type_text = "STRING"
    }
  }

  return_type {
    type_text = "BOOLEAN"
  }

  body = <<-SQL
    EXISTS (
      SELECT 1
      FROM ${var.catalog_name}.config.asset_group_map m
      WHERE m.asset_id = asset_id
        AND m.is_active = true
        AND is_account_group_member(m.entra_group_id)
    )
    OR
    EXISTS (
      SELECT 1
      FROM ${var.catalog_name}.config.asset_group_map m
      WHERE m.scope = 'GLOBAL'
        AND m.is_active = true
        AND is_account_group_member(m.entra_group_id)
    )
  SQL
}

# ── Pattern 4: MSVC — no row filter ──────────────────────────────────────────
# MSVC access is controlled by schema-level GRANT in grants.tf.
# The MSVC-Approved Entra group gets SELECT on the entire euh_BLP schema.
# No row filter function needed — schema grant IS the access control.

# ── UAT: Column masking for developer access to euh_prod_mirror ───────────────
# Developers in uat-developers group see masked values.
# Business owners in uat-business-owners group see real prod values.
# Applied to sensitive columns in euh_prod_mirror schemas via ALTER COLUMN.

resource "databricks_sql_function" "mask_pii" {
  catalog_name = var.catalog_name   # applied against uat_catalog
  schema_name  = "platform_config"
  name         = "mask_pii"
  comment      = "UAT column masking — developers see MASKED, business owners see real values"

  input_params {
    parameters {
      name      = "val"
      type_text = "STRING"
    }
  }

  return_type {
    type_text = "STRING"
  }

  body = <<-SQL
    CASE
      WHEN is_account_group_member('${var.entra_group_uat_business}') THEN val
      ELSE '***MASKED***'
    END
  SQL
}
