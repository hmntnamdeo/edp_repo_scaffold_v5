# Unity Catalog — Handoff Contract

## Ownership boundary

| Object | Owner | Managed by |
|---|---|---|
| Unity Catalog metastore | Central platform ops | Outside this repo |
| Catalogs (`dev_catalog`, `uat_catalog`, `prod_catalog`) | Central platform ops | Outside this repo |
| Schemas within catalogs | EDP programme | `schemas.tf` in this repo |
| Grants on schemas | EDP programme | `grants.tf` in this repo |
| Row filter functions | EDP programme | `row_filters.tf` in this repo |

Catalogs are tied to fixed domains under the mesh architecture. Their lifecycle
is a governance decision owned above programme level. EDP Terraform references
catalogs by name — it never creates, modifies, or destroys them.

## What central platform ops must provision before EDP Terraform runs

For each environment (dev / uat / prod), central platform ops must confirm:

- [ ] Catalog exists with the agreed name (`dev_catalog` / `uat_catalog` / `prod_catalog`)
- [ ] EDP pipeline service principal (`edp-pipeline-spn`) has `USE_CATALOG` on the catalog
- [ ] EDP Terraform service principal has `CREATE_SCHEMA` on the catalog
- [ ] Catalog is attached to the correct Databricks workspace for that environment

## What EDP provides back to central platform ops

After each Terraform apply, EDP notifies platform ops of:
- Schemas created (list from `terraform output`)
- Service principals and groups granted access
- Any catalog-level permissions requested that exceed current grants

## Catalog names by environment

| Environment | Catalog name | Databricks workspace |
|---|---|---|
| Dev | `dev_catalog` | `https://adb-dev.azuredatabricks.net` |
| UAT | `uat_catalog` | `https://adb-uat.azuredatabricks.net` |
| Prod | `prod_catalog` | `https://adb-prod.azuredatabricks.net` |

These names are fixed. If central platform ops provisions under different names,
update `envs/<env>.tfvars` — the `catalog_name` variable is the only coupling point.
