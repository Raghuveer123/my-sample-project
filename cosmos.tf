locals {
  primary_cluster_location = var.is_primary ? null : data.azurerm_cosmosdb_postgresql_cluster.primary[0].location
  primary_cluster_id       = var.is_primary ? null : data.azurerm_cosmosdb_postgresql_cluster.primary[0].id
}

module "cosmosdb_postgresql_cluster" {
  source                           = "./modules/cosmosdb_postgresql_cluster"
  name                             = var.cluster_name
  resource_group_name              = azurerm_resource_group.rg.name
  location                         = var.region
  password                         = random_password.cosmosdb_postgresql_passwords.result
  coordinator_storage_quota_in_mb  = 262144
  coordinator_vcore_count          = 2
  node_count                       = 2
  node_storage_quota_in_mb         = 262144
  node_vcores                      = 2
  node_server_edition              = "MemoryOptimized"
  coordinator_public_ip_access_enabled = var.is_primary ? false : true
  citus_version                        = "12.1"
  sql_version                          = "16"

  source_location      = local.primary_cluster_location
  source_resource_id   = local.primary_cluster_id
}
