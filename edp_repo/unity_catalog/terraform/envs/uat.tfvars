# unity_catalog/terraform/envs/uat.tfvars
environment  = "uat"
catalog_name = "uat_catalog"
databricks_host = "https://adb-uat.azuredatabricks.net"

pipeline_spn = "edp-pipeline-spn@yourtenant.onmicrosoft.com"

entra_group_msvc_approved  = "<entra-group-object-id-msvc-approved>"
entra_group_platform_admin = "<entra-group-object-id-platform-admin>"
entra_group_uat_business   = "<entra-group-object-id-uat-business-owners>"
entra_group_uat_developers = "<entra-group-object-id-uat-developers>"
entra_group_data_lead      = "<entra-group-object-id-data-lead>"
