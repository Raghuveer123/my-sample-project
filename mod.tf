# modules/cosmosdb_postgresql_cluster/main.tf
variable "name" {}
variable "resource_group_name" {}
variable "location" {}
variable "source_location" { default = null }
variable "source_resource_id" { default = null }
variable "password" {}
variable "coordinator_storage_quota_in_mb" {}
variable "coordinator_vcore_count" {}
variable "node_count" {}
variable "node_storage_quota_in_mb" {}
variable "node_vcores" {}
variable "node_server_edition" {}
variable "coordinator_public_ip_access_enabled" {}
variable "citus_version" {}
variable "sql_version" {}

resource "azurerm_cosmosdb_postgresql_cluster" "cluster" {
  name                            = var.name
  resource_group_name             = var.resource_group_name
  location                        = var.location
  administrator_login_password    = var.password
  coordinator_storage_quota_in_mb = var.coordinator_storage_quota_in_mb
  coordinator_vcore_count         = var.coordinator_vcore_count
  node_count                      = var.node_count
  node_storage_quota_in_mb        = var.node_storage_quota_in_mb
  node_vcores                     = var.node_vcores
  node_server_edition             = var.node_server_edition
  coordinator_public_ip_access_enabled = var.coordinator_public_ip_access_enabled
  citus_version                        = var.citus_version
  sql_version                          = var.sql_version

  # Conditional fields for read replica
  source_location      = var.source_location
  source_resource_id   = var.source_resource_id
}
