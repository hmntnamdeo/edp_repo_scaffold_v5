# unity_catalog/terraform/envs/dev.tfvars
environment  = "dev"
catalog_name = "dev_catalog"
databricks_host = "https://adb-dev.azuredatabricks.net"

pipeline_spn = "edp-pipeline-spn-dev@yourtenant.onmicrosoft.com"

entra_group_msvc_approved  = "<entra-group-object-id-msvc-approved>"
entra_group_platform_admin = "<entra-group-object-id-platform-admin>"
entra_group_uat_business   = ""   # not applicable in dev
entra_group_uat_developers = ""   # not applicable in dev
entra_group_data_lead      = "<entra-group-object-id-data-lead>"
