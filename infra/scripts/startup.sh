#!/bin/bash
apt-get update -y
apt-get install -y docker.io awscli

systemctl start docker
systemctl enable docker

# Login a ECR
aws ecr get-login-password --region ${aws_region} | \
  docker login --username AWS --password-stdin ${ecr_registry}

# Baja y ejecuta la imagen
docker pull ${ecr_registry}/${image_name}:latest

# Aplica las migraciones ANTES de servir tráfico.
# Se ejecuta en un contenedor de usar-y-tirar (--rm), reutilizando la
# misma imagen: mismo código, mismas dependencias, cero duplicación.
docker run --rm \
  -e DATABASE_URL="${db_url}" \
  ${ecr_registry}/${image_name}:latest \
  alembic upgrade head

docker run -d \
  --name monitored-api \
  --restart always \
  -p 8000:8000 \
  -e DATABASE_URL="${db_url}" \
  ${ecr_registry}/${image_name}:latest