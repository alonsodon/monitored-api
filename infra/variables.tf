# infra/variables.tf
variable "db_username" {
  type    = string
  default = "postgres"
}

variable "db_password" {
  type      = string
  sensitive = true # Terraform no lo mostrará en logs
}