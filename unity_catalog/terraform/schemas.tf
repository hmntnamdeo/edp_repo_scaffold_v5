# unity_catalog/terraform/schemas.tf
#
# Creates EDP schemas within the pre-existing Unity Catalog catalogs.
#
# CATALOG OWNERSHIP:
#   Catalogs are provisioned by central platform operations — they are NOT managed
#   here. Catalogs are tied to fixed domains under the mesh architecture and their
#   lifecycle is owned above the programme level.
#   This Terraform scope starts at schemas. Catalogs are referenced by name via
#   var.catalog_name (injected from tfvars) — they must already exist before
#   this plan runs.
#
# WHAT THIS FILE MANAGES:
#   Schema creation only. Tables are created on the fly by notebooks — not here.
#   Each Terraform target (dev/uat/prod) manages schemas for its own catalog only.
#   Run per environment: terraform apply -var-file=envs/<env>.tfvars
#
# Schema naming rules:
#   Landing dev:   landing_[SRC]_[ENV]      e.g. landing_BLP_A59
#   Landing prod:  landing_[SRC]            e.g. landing_BLP
#   EUH dev:       euh_[SRC]_[ENV]          e.g. euh_BLP_A59
#   EUH UAT:       euh_prod_mirror_[SRC]    e.g. euh_prod_mirror_BLP
#   EUH prod:      euh_[SRC]               e.g. euh_BLP
#   Curated dev:   feat_[FEATURE]_[DOMAIN]  e.g. feat_spend_v2_sourcing  (ephemeral — not here)
#   Curated UAT:   stable_[DOMAIN]          e.g. stable_sourcing
#   Curated prod:  [DOMAIN]                 e.g. sourcing

terraform {
  required_providers {
    databricks = {
      source  = "databricks/databricks"
      version = "~> 1.40"
    }
  }
}

provider "databricks" {
  host  = var.databricks_host
  token = var.databricks_token
}

# ── Variables ─────────────────────────────────────────────────────────────────

variable "databricks_host"  { type = string }
variable "databricks_token" { type = string, sensitive = true }
variable "environment"      { type = string }   # dev | uat | prod
variable "catalog_name"     { type = string }   # pre-existing catalog — not created here

locals {
  # Source IDs — registered in config/source_systems.yml
  source_ids = ["BLP", "ARB", "CLM", "KBL", "FIN", "AIF"]

  # Six curated domains — fixed. No new domains without an ADR.
  curated_domains = ["plan", "sourcing", "deliver", "master", "config", "mapping"]

  # Dev env ID
  dev_env_id = "A59"
}

# ── Dev schemas ───────────────────────────────────────────────────────────────
# Applied when var.environment = "dev"

resource "databricks_schema" "landing" {
  for_each     = var.environment == "dev" ? toset(local.source_ids) : toset([])
  catalog_name = var.catalog_name
  name         = "landing_${each.key}_${local.dev_env_id}"
  comment      = "Landing — ${each.key} — dev env ${local.dev_env_id}"
}

resource "databricks_schema" "euh_dev" {
  for_each     = var.environment == "dev" ? toset(local.source_ids) : toset([])
  catalog_name = var.catalog_name
  name         = "euh_${each.key}_${local.dev_env_id}"
  comment      = "EUH — ${each.key} — dev env ${local.dev_env_id}"
}

resource "databricks_schema" "platform_config_dev" {
  count        = var.environment == "dev" ? 1 : 0
  catalog_name = var.catalog_name
  name         = "platform_config"
  comment      = "Platform orchestration metadata — dev"
}

# Note: Curated dev schemas (feat_[feature]_[domain]) are ephemeral.
# Created and dropped by uat_provision_schema.py — not managed here.

# ── UAT schemas ───────────────────────────────────────────────────────────────
# Applied when var.environment = "uat"

resource "databricks_schema" "euh_prod_mirror" {
  for_each     = var.environment == "uat" ? toset(local.source_ids) : toset([])
  catalog_name = var.catalog_name
  name         = "euh_prod_mirror_${each.key}"
  comment      = "Full prod EUH copy — ${each.key} — nightly 02:00 UTC — read only"
}

resource "databricks_schema" "curated_stable" {
  for_each     = var.environment == "uat" ? toset(local.curated_domains) : toset([])
  catalog_name = var.catalog_name
  name         = "stable_${each.key}"
  comment      = "Curated stable baseline — ${each.key} — nightly from euh_prod_mirror"
}

resource "databricks_schema" "platform_config_uat" {
  count        = var.environment == "uat" ? 1 : 0
  catalog_name = var.catalog_name
  name         = "platform_config"
  comment      = "Platform orchestration metadata — UAT"
}

# Note: UAT feature schemas (feat_[feature]_[domain]) are ephemeral.
# Created and dropped by uat_provision_schema.py — not managed here.

# ── Prod schemas ──────────────────────────────────────────────────────────────
# Applied when var.environment = "prod"

resource "databricks_schema" "landing_prod" {
  for_each     = var.environment == "prod" ? toset(local.source_ids) : toset([])
  catalog_name = var.catalog_name
  name         = "landing_${each.key}"
  comment      = "Landing — ${each.key} — production"
}

resource "databricks_schema" "euh_prod" {
  for_each     = var.environment == "prod" ? toset(local.source_ids) : toset([])
  catalog_name = var.catalog_name
  name         = "euh_${each.key}"
  comment      = "EUH — ${each.key} — EDAM field names — production"
}

resource "databricks_schema" "curated_prod" {
  for_each     = var.environment == "prod" ? toset(local.curated_domains) : toset([])
  catalog_name = var.catalog_name
  name         = each.key
  comment      = "Curated domain — ${each.key} — production"
}

resource "databricks_schema" "platform_config_prod" {
  count        = var.environment == "prod" ? 1 : 0
  catalog_name = var.catalog_name
  name         = "platform_config"
  comment      = "Platform orchestration metadata — production"
}
