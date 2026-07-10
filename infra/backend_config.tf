# infra/backend_config.tf

terraform {
  backend "s3" {
    bucket         = "alonsodon-terraform-state-monitored-api"
    key            = "monitored-api/terraform.tfstate"
    region         = "eu-central-1"
    dynamodb_table = "terraform-state-lock"
    encrypt        = true
  }
}