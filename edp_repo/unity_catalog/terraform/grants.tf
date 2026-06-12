# unity_catalog/terraform/grants.tf
# Manages schema-level and catalog-level GRANTS only.
# Row-level security is NOT here — it is handled by:
#   1. row_filters.tf  — deploys the filter functions
#   2. Notebooks       — bind filters to tables on first run (tables are created on the fly)
#   3. Migration scripts — rebind filters when security changes post-deploy
#
# Entra ID group IDs are passed in via tfvars per environment.
# Never hardcode group IDs in .tf files — they differ per environment.

# ── Variables ─────────────────────────────────────────────────────────────────

variable "pipeline_spn"               { type = string }  # pipeline service principal
variable "entra_group_msvc_approved"  { type = string }  # MSVC-Approved group object ID
variable "entra_group_platform_admin" { type = string }  # platform admin group
variable "entra_group_uat_business"   { type = string }  # UAT business owner group
variable "entra_group_uat_developers" { type = string }  # UAT developer group (masked access)
variable "entra_group_data_lead"      { type = string }  # data lead group

# ── Catalog-level grants ──────────────────────────────────────────────────────

# Pipeline SPN needs USE CATALOG to read/write tables
resource "databricks_grants" "catalog_pipeline" {
  catalog = var.catalog_name

  grant {
    principal  = var.pipeline_spn
    privileges = ["USE_CATALOG", "CREATE_SCHEMA"]
  }

  grant {
    principal  = var.entra_group_platform_admin
    privileges = ["USE_CATALOG"]
  }
}

# ── Prod: EUH schema grants ───────────────────────────────────────────────────
# MSVC pattern: schema-level SELECT grant to MSVC-Approved Entra group.
# No row filter — the schema grant IS the access control for this pattern.

resource "databricks_grants" "prod_euh_msvc_schema" {
  # Only applies to euh_BLP schema (MSVC source)
  # Other EUH schemas are accessed only by the pipeline SPN
  schema = "${var.catalog_name}.euh_BLP"

  grant {
    principal  = var.entra_group_msvc_approved
    privileges = ["SELECT", "USE_SCHEMA"]
  }

  grant {
    principal  = var.pipeline_spn
    privileges = ["SELECT", "USE_SCHEMA", "CREATE_TABLE", "MODIFY"]
  }
}

# Pipeline SPN access to all EUH schemas
resource "databricks_grants" "prod_euh_pipeline" {
  for_each = toset([for s in local.source_ids : s if s != "BLP"])
  schema   = "${var.catalog_name}.euh_${each.key}"

  grant {
    principal  = var.pipeline_spn
    privileges = ["SELECT", "USE_SCHEMA", "CREATE_TABLE", "MODIFY"]
  }
}

# ── Prod: Curated domain schema grants ───────────────────────────────────────
# These are USE_SCHEMA only — row-level access is controlled by row filters on tables.
# Direct SELECT on schema is NOT granted to end users here; the row filter
# on each table enforces data visibility per the four security patterns.

resource "databricks_grants" "prod_curated_pipeline" {
  for_each = toset(local.curated_domains)
  schema   = "${var.catalog_name}.${each.key}"

  grant {
    principal  = var.pipeline_spn
    privileges = ["USE_SCHEMA", "CREATE_TABLE", "MODIFY", "SELECT"]
  }

  grant {
    principal  = var.entra_group_platform_admin
    privileges = ["USE_SCHEMA", "SELECT"]
  }
}

# ── UAT: Access control for euh_prod_mirror schemas ──────────────────────────
# Business owners: full SELECT (they sign off UAT with real data)
# Developers: USE_SCHEMA only — column masking applied by row_filters.tf
# Pipeline SPN: full access for provisioning

resource "databricks_grants" "uat_euh_mirror_business" {
  for_each = toset(local.source_ids)
  schema   = "${var.catalog_name}.euh_prod_mirror_${each.key}"

  grant {
    principal  = var.entra_group_uat_business
    privileges = ["SELECT", "USE_SCHEMA"]
  }

  grant {
    principal  = var.entra_group_uat_developers
    privileges = ["USE_SCHEMA"]   # SELECT granted via masking policy — data is masked
  }

  grant {
    principal  = var.pipeline_spn
    privileges = ["USE_SCHEMA", "CREATE_TABLE", "MODIFY", "SELECT"]
  }
}

# UAT: Developers cannot create schemas — only pipeline SPN can
resource "databricks_grants" "uat_catalog_schema_create" {
  catalog = var.catalog_name

  grant {
    principal  = var.pipeline_spn
    privileges = ["CREATE_SCHEMA", "USE_CATALOG"]
  }

  grant {
    principal  = var.entra_group_uat_business
    privileges = ["USE_CATALOG"]
  }

  grant {
    principal  = var.entra_group_uat_developers
    privileges = ["USE_CATALOG"]
  }
}

# ── Platform config schema grants ─────────────────────────────────────────────
# config schema holds: orchestration_config, migration_history, lob_group_map,
# legal_entity_group_map, asset_group_map
# Platform admin and pipeline SPN only — no end user access

resource "databricks_grants" "prod_config_schema" {
  schema = "${var.catalog_name}.config"

  grant {
    principal  = var.pipeline_spn
    privileges = ["USE_SCHEMA", "CREATE_TABLE", "MODIFY", "SELECT"]
  }

  grant {
    principal  = var.entra_group_platform_admin
    privileges = ["USE_SCHEMA", "SELECT"]
  }

  grant {
    principal  = var.entra_group_data_lead
    privileges = ["USE_SCHEMA", "SELECT"]
  }
}
