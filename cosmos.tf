provider "azurerm" {
  features {}
}

# Variables
variable "location" {
  default = "eastus"
}

variable "resource_group_name" {
  default = "rg-cosmosdb-pgsql"
}

variable "key_vault_name" {
  default = "kv-cosmosdb-pgsql"
}

variable "cosmosdb_name" {
  default = "cosmosdb-pgsql"
}

variable "vnet_name" {
  default = "vnet-cosmosdb"
}

variable "subnet_name" {
  default = "subnet-cosmosdb"
}

# Resource Group
resource "azurerm_resource_group" "main" {
  name     = var.resource_group_name
  location = var.location
}

# Virtual Network
resource "azurerm_virtual_network" "main" {
  name                = var.vnet_name
  address_space       = ["10.0.0.0/16"]
  location            = azurerm_resource_group.main.location
  resource_group_name = azurerm_resource_group.main.name
}

# Subnet for Private Link
resource "azurerm_subnet" "main" {
  name                 = var.subnet_name
  resource_group_name  = azurerm_resource_group.main.name
  virtual_network_name = azurerm_virtual_network.main.name
  address_prefixes     = ["10.0.1.0/24"]
  enforce_private_link_endpoint_network_policies = true
}

# Private DNS Zone (Optional - Only if DNS required)
resource "azurerm_private_dns_zone" "main" {
  name                = "privatelink.postgres.database.azure.com"
  resource_group_name = azurerm_resource_group.main.name
}

# Private DNS Link (Optional)
resource "azurerm_private_dns_zone_virtual_network_link" "main" {
  name                  = "vnet-link"
  resource_group_name   = azurerm_resource_group.main.name
  private_dns_zone_name = azurerm_private_dns_zone.main.name
  virtual_network_id    = azurerm_virtual_network.main.id
}

# Key Vault
resource "azurerm_key_vault" "main" {
  name                        = var.key_vault_name
  location                    = azurerm_resource_group.main.location
  resource_group_name         = azurerm_resource_group.main.name
  tenant_id                   = data.azurerm_client_config.current.tenant_id
  sku_name                    = "standard"

  access_policy {
    tenant_id = data.azurerm_client_config.current.tenant_id
    object_id = data.azurerm_client_config.current.object_id

    secret_permissions = ["get", "set", "delete", "list"]
  }
}

# Store Admin Password in Key Vault
resource "azurerm_key_vault_secret" "admin_password" {
  name         = "cosmosdb-admin-password"
  value        = random_password.admin_password.result
  key_vault_id = azurerm_key_vault.main.id
}

# Generate Random Password
resource "random_password" "admin_password" {
  length  = 16
  special = true
}

# Fetch the password dynamically from Key Vault
data "azurerm_key_vault_secret" "admin_password" {
  name         = azurerm_key_vault_secret.admin_password.name
  key_vault_id = azurerm_key_vault.main.id
}

# CosmosDB for PostgreSQL
resource "azurerm_cosmosdb_postgresql_cluster" "main" {
  name                = var.cosmosdb_name
  resource_group_name = azurerm_resource_group.main.name
  location            = azurerm_resource_group.main.location

  administrator_login   = "adminuser"
  administrator_password = data.azurerm_key_vault_secret.admin_password.value
  sku_name              = "Standard_D4s_v3"
  postgres_version      = "15"

  storage_mb            = 102400
  backup_retention_days = 7
  geo_redundant_backup_enabled = false

  network_configuration {
    subnet_id = azurerm_subnet.main.id
  }

  tags = {
    environment = "production"
  }
}

# Private Endpoint
resource "azurerm_private_endpoint" "main" {
  name                = "pe-cosmosdb"
  location            = azurerm_resource_group.main.location
  resource_group_name = azurerm_resource_group.main.name
  subnet_id           = azurerm_subnet.main.id

  private_service_connection {
    name                           = "psc-cosmosdb"
    private_connection_resource_id = azurerm_cosmosdb_postgresql_cluster.main.id
    is_manual_connection           = false
  }
}
