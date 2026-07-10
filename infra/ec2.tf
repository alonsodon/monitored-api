# infra/ec2.tf
resource "aws_instance" "app" {
  ami                    = data.aws_ami.ubuntu.id
  instance_type          = "t3.micro"
  vpc_security_group_ids = [aws_security_group.ec2.id]
  subnet_id              = aws_subnet.public.id
  iam_instance_profile   = aws_iam_instance_profile.ec2_profile.name
  key_name               = "monitored-api-key" # tu par de claves SSH

  user_data = templatefile("${path.module}/scripts/startup.sh", {
    ecr_registry = "${data.aws_caller_identity.current.account_id}.dkr.ecr.eu-central-1.amazonaws.com"
    image_name   = "monitored-api"
    db_url       = "postgresql://${var.db_username}:${var.db_password}@${aws_db_instance.postgres.endpoint}/monitored_api"
    aws_region   = "eu-central-1"
  })

  tags = { Name = "monitored-api-server" }
}

output "app_public_ip" {
  value = aws_instance.app.public_ip
}