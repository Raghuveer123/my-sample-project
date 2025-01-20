provider "azurerm" {
  features {}
}

resource "azurerm_resource_group" "rg" {
  name     = "testrg"
  location = var.region
}

resource "random_password" "cosmosdb_postgresql_passwords" {
  length      = 24
  min_upper   = 6
  min_lower   = 4
  min_numeric = 6
  special     = false
}

data "azurerm_cosmosdb_postgresql_cluster" "primary" {
  name                = var.primary_cluster_name
  resource_group_name = var.primary_resource_group_name
  count               = var.is_primary ? 0 : 1
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

  source_location      = var.is_primary ? null : data.azurerm_cosmosdb_postgresql_cluster.primary[0].location
  source_resource_id   = var.is_primary ? null : data.azurerm_cosmosdb_postgresql_cluster.primary[0].id
}
