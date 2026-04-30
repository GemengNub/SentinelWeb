# Sentinel Hybrid Deploy (Vercel + AWS)

This setup keeps your current architecture:
- `frontend` on Vercel
- `backend` API, `celery-worker`, and `celery-beat` on AWS ECS Fargate
- PostgreSQL on Amazon RDS
- Redis on Amazon ElastiCache

## 1) Prerequisites

- AWS account + IAM user/role with ECS, ECR, IAM, RDS, ElastiCache, ALB, Secrets Manager access
- AWS CLI v2 configured (`aws configure`)
- Docker installed locally
- A domain for API (recommended), for example `api.sentinel.example.com`

PowerShell variables used below:

```powershell
$env:AWS_REGION = "us-east-1"
$ACCOUNT_ID = aws sts get-caller-identity --query Account --output text
$ECR_REPO = "sentinel-backend"
$CLUSTER = "sentinel-cluster"
$SERVICE_API = "sentinel-api"
$SERVICE_WORKER = "sentinel-worker"
$SERVICE_BEAT = "sentinel-beat"
```

## 2) Build and push backend image to ECR

```powershell
aws ecr create-repository --repository-name $ECR_REPO --region $env:AWS_REGION
aws ecr get-login-password --region $env:AWS_REGION | docker login --username AWS --password-stdin "$ACCOUNT_ID.dkr.ecr.$env:AWS_REGION.amazonaws.com"

docker build -t "$ECR_REPO`:latest" backend
docker tag "$ECR_REPO`:latest" "$ACCOUNT_ID.dkr.ecr.$env:AWS_REGION.amazonaws.com/$ECR_REPO`:latest"
docker push "$ACCOUNT_ID.dkr.ecr.$env:AWS_REGION.amazonaws.com/$ECR_REPO`:latest"
```

## 3) Create data services

Create these in AWS console:
- RDS PostgreSQL (private subnets, SG only from ECS tasks)
- ElastiCache Redis (private subnets, SG only from ECS tasks)

Collect:
- `RDS_ENDPOINT` (host)
- `REDIS_ENDPOINT` (host)

## 4) Store runtime secrets

Create secrets in Secrets Manager:

```powershell
aws secretsmanager create-secret --name sentinel/prod/database-url --secret-string "postgresql+asyncpg://<db_user>:<db_password>@<RDS_ENDPOINT>:5432/sentinel" --region $env:AWS_REGION
aws secretsmanager create-secret --name sentinel/prod/redis-url --secret-string "redis://<REDIS_ENDPOINT>:6379/0" --region $env:AWS_REGION
aws secretsmanager create-secret --name sentinel/prod/celery-broker-url --secret-string "redis://<REDIS_ENDPOINT>:6379/1" --region $env:AWS_REGION
aws secretsmanager create-secret --name sentinel/prod/celery-result-backend --secret-string "redis://<REDIS_ENDPOINT>:6379/2" --region $env:AWS_REGION
aws secretsmanager create-secret --name sentinel/prod/openweather-api-key --secret-string "<OPENWEATHER_API_KEY>" --region $env:AWS_REGION
```

## 5) IAM roles for ECS tasks

Create/verify `ecsTaskExecutionRole` (standard ECS execution role):

```powershell
aws iam create-role --role-name ecsTaskExecutionRole --assume-role-policy-document file://infra/aws/iam/ecs-tasks-trust-policy.json
aws iam attach-role-policy --role-name ecsTaskExecutionRole --policy-arn arn:aws:iam::aws:policy/service-role/AmazonECSTaskExecutionRolePolicy
```

Attach inline secrets policy (edit placeholders first):

```powershell
aws iam put-role-policy --role-name ecsTaskExecutionRole --policy-name sentinel-secrets --policy-document file://infra/aws/iam/ecs-task-execution-secrets-policy.json
```

Create an application task role (if you do not already have one):

```powershell
aws iam create-role --role-name sentinelTaskRole --assume-role-policy-document file://infra/aws/iam/ecs-tasks-trust-policy.json
```

## 6) Register task definitions

Before running these commands, replace placeholders in:
- `infra/aws/ecs/taskdef-api.json`
- `infra/aws/ecs/taskdef-worker.json`
- `infra/aws/ecs/taskdef-beat.json`

```powershell
aws ecs register-task-definition --cli-input-json file://infra/aws/ecs/taskdef-api.json --region $env:AWS_REGION
aws ecs register-task-definition --cli-input-json file://infra/aws/ecs/taskdef-worker.json --region $env:AWS_REGION
aws ecs register-task-definition --cli-input-json file://infra/aws/ecs/taskdef-beat.json --region $env:AWS_REGION
```

## 7) Create ECS cluster and services

```powershell
aws ecs create-cluster --cluster-name $CLUSTER --region $env:AWS_REGION
```

Create services:
- API service (`sentinel-api`) with Application Load Balancer target group:
  - target type `ip`
  - health check path `/api/v1/health`
  - listener 443 with ACM certificate
- Worker service (`sentinel-worker`) without load balancer
- Beat service (`sentinel-beat`) without load balancer

Important WebSocket setting:
- For ALB, increase idle timeout from default `60` to at least `300` seconds.

## 8) Run DB migration once

Use a one-off task with the API task definition and override command:

```powershell
aws ecs run-task `
  --cluster $CLUSTER `
  --task-definition sentinel-api `
  --launch-type FARGATE `
  --network-configuration "awsvpcConfiguration={subnets=[subnet-aaa,subnet-bbb],securityGroups=[sg-ecs],assignPublicIp=DISABLED}" `
  --overrides file://infra/aws/ecs/run-migration-overrides.json `
  --region $env:AWS_REGION
```

## 9) Wire frontend on Vercel

Set Vercel environment variables from [`frontend/.env.production.example`](../../frontend/.env.production.example):

- `VITE_API_URL=https://api.sentinel.example.com/api/v1`
- `VITE_WS_URL=wss://api.sentinel.example.com/api/v1/ws`

Deploy frontend:
- Project root: `frontend/`
- Build command: `npm run build`
- Output directory: `dist`

## 10) Validate end-to-end

Health:

```text
https://api.sentinel.example.com/api/v1/health
```

Docs:

```text
https://api.sentinel.example.com/docs
```

WebSocket:

```text
wss://api.sentinel.example.com/api/v1/ws
```

## Notes

- Rotate any existing credentials that were previously committed in local config files.
- Keep local `docker-compose` for development unchanged.
- For production hardening: private subnets for ECS/RDS/Redis, least-privilege SGs, CloudWatch alarms, and WAF on ALB.
