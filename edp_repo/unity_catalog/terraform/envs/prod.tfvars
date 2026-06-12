# unity_catalog/terraform/envs/prod.tfvars
# Production environment — Terraform variable values
# Catalog is pre-provisioned by central platform ops — not managed by this repo.
# Entra group object IDs come from the Entra ID audit (prerequisite before security migration)
# Never commit real secrets — databricks_token is injected via CI/CD secret at deploy time

environment  = "prod"
catalog_name = "prod_catalog"
databricks_host = "https://adb-prod.azuredatabricks.net"

# Service principal
pipeline_spn = "edp-pipeline-spn@yourtenant.onmicrosoft.com"

# Catalog is pre-provisioned by central platform ops — not managed by this repo.
# Entra group object IDs — populated after Entra ID audit (R8 risk mitigation)
entra_group_msvc_approved  = "<entra-group-object-id-msvc-approved>"
entra_group_platform_admin = "<entra-group-object-id-platform-admin>"
entra_group_uat_business   = ""   # not used in prod tfvars
entra_group_uat_developers = ""   # not used in prod tfvars
entra_group_data_lead      = "<entra-group-object-id-data-lead>"
