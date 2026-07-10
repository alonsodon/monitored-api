#!/bin/bash
# scripts/check_aws.sh
# Verifica qué tengo encendido en general y costes del mes actual

echo "--- EC2 (instancias corriendo) ---"
aws ec2 describe-instances \
  --filters "Name=instance-state-name,Values=running,stopped" \
  --query "Reservations[].Instances[].[InstanceId,InstanceType,State.Name,Tags[?Key=='Name'].Value|[0]]" \
  --output table

echo ""
echo "--- RDS (bases de datos) ---"
aws rds describe-db-instances \
  --query "DBInstances[].[DBInstanceIdentifier,DBInstanceClass,DBInstanceStatus]" \
  --output table

echo ""
echo "--- ECR (imágenes almacenadas) ---"
aws ecr describe-repositories --query "repositories[].repositoryName" --output table

echo ""
echo "--- S3 (buckets con tags) ---"
for bucket in $(aws s3api list-buckets --query "Buckets[].Name" --output text); do
  tags=$(aws s3api get-bucket-tagging --bucket "$bucket" --query "TagSet[?Key=='Name'].Value|[0]" --output text 2>/dev/null)
  echo "$bucket	${tags:-Sin tags}"
done | column -t   

echo ""
echo "--- DynamoDB (tablas) ---"
aws dynamodb list-tables \
  --query "TableNames[]" \
  --output table   

echo ""
echo "--- VPCs (no gratis en sí, pero delata que hay red montada) ---"
aws ec2 describe-vpcs \
  --query "Vpcs[].[VpcId,Tags[?Key=='Name'].Value|[0]]" \
  --output table

START=$(date +%Y-%m-01)
END=$(date -v+1m -v1d +%Y-%m-%d 2>/dev/null || date -d "next month" +%Y-%m-01)
echo ""
echo "--- Visualizar costes y uso ---"
aws ce get-cost-and-usage \
  --time-period Start=${START},End=${END} \
  --granularity MONTHLY \
  --metrics "UnblendedCost" \
  --group-by Type=DIMENSION,Key=SERVICE \
  --query "ResultsByTime[].Groups[?Metrics.UnblendedCost.Amount!='0'].[Keys[0],Metrics.UnblendedCost.Amount]" \
  --output table