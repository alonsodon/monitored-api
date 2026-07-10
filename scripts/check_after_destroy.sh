#!/bin/bash
# scripts/check_after_destroy.sh
# Verifica que la infraestructura "de coste" está destruida
# y que la permanente (backend + ECR) sigue intacta.

echo "=== Recursos que DEBEN estar destruidos ==="

VPC=$(aws ec2 describe-vpcs --filters "Name=tag:Name,Values=monitored-api-vpc" \
  --query "Vpcs[].VpcId" --output text)
if [ -z "$VPC" ]; then
  echo "✅ VPC: destruida"
else
  echo "❌ VPC: TODAVÍA EXISTE ($VPC)"
fi

RDS_STATUS=$(aws rds describe-db-instances --db-instance-identifier monitored-api-db \
  --query "DBInstances[].DBInstanceStatus" --output text 2>/dev/null)
if [ -z "$RDS_STATUS" ]; then
  echo "✅ RDS: destruida"
else
  echo "❌ RDS: TODAVÍA EXISTE (estado: $RDS_STATUS)"
fi

EC2_RUNNING=$(aws ec2 describe-instances \
  --filters "Name=tag:Name,Values=monitored-api-server" "Name=instance-state-name,Values=running" \
  --query "Reservations[].Instances[].InstanceId" --output text)
if [ -z "$EC2_RUNNING" ]; then
  echo "✅ EC2: sin instancias corriendo"
else
  echo "❌ EC2: TODAVÍA CORRIENDO ($EC2_RUNNING)"
fi

echo ""
echo "=== Recursos que DEBEN seguir vivos ==="

if aws s3 ls "s3://alonsodon-terraform-state-monitored-api/" > /dev/null 2>&1; then
  echo "✅ S3 (state): vivo"
else
  echo "❌ S3 (state): NO ENCONTRADO — ¡esto sería grave!"
fi

DYNAMO_STATUS=$(aws dynamodb describe-table --table-name terraform-state-lock \
  --query "Table.TableStatus" --output text 2>/dev/null)
if [ "$DYNAMO_STATUS" = "ACTIVE" ]; then
  echo "✅ DynamoDB (lock): vivo"
else
  echo "❌ DynamoDB (lock): NO ENCONTRADO O INACTIVO"
fi

ECR=$(aws ecr describe-repositories --repository-names monitored-api \
  --query "repositories[].repositoryName" --output text 2>/dev/null)
if [ "$ECR" = "monitored-api" ]; then
  echo "✅ ECR: vivo"
else
  echo "❌ ECR: NO ENCONTRADO"
fi