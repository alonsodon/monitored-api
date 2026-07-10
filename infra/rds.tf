# infra/rds.tf

# Grupo de subredes: le dice a RDS en qué subredes (privadas) puede vivir
resource "aws_db_subnet_group" "main" {
  name       = "monitored-api-subnet-group"
  subnet_ids = [aws_subnet.private_a.id, aws_subnet.private_b.id]
}

# Security group de la RDS: solo acepta conexiones DESDE la EC2
resource "aws_security_group" "rds" {
  name   = "monitored-api-rds-sg"
  vpc_id = aws_vpc.main.id

  ingress {
    from_port       = 5432
    to_port         = 5432
    protocol        = "tcp"
    security_groups = [aws_security_group.ec2.id] # ← solo desde el SG de la EC2
  }
}

# La instancia de PostgreSQL
resource "aws_db_instance" "postgres" {
  identifier        = "monitored-api-db"
  engine            = "postgres"
  engine_version    = "15"          # major 15; RDS elige la última minor disponible
  instance_class    = "db.t3.micro" # Free Tier eligible
  allocated_storage = 20
  storage_type      = "gp2"

  db_name  = "monitored_api"
  username = var.db_username
  password = var.db_password # en producción real: AWS Secrets Manager

  db_subnet_group_name   = aws_db_subnet_group.main.name
  vpc_security_group_ids = [aws_security_group.rds.id]

  skip_final_snapshot = true  # para desarrollo (en prod: false)
  deletion_protection = false # idem

  tags = { Name = "monitored-api-db" }
}

output "db_endpoint" {
  value     = aws_db_instance.postgres.endpoint
  sensitive = true
}