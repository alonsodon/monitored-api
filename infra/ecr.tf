# infra/ecr.tf
resource "aws_ecr_repository" "monitored_api" {
  name                 = "monitored-api"
  image_tag_mutability = "MUTABLE"

  image_scanning_configuration {
    scan_on_push = true
  }
}