# AWS Deployment (Terraform + CI/CD)

Infrastructure-as-Code for running GOD MODE AI / AGNI on AWS ECS Fargate.

## What it provisions

```
Internet
   │
   ▼
CloudFront ── S3 (static / Flutter web)
   │
Route53 (optional) ─► ALB (public subnets)
                         │  /health, WebSocket upgrade
                         ▼
                ECS Fargate service  ── api task (Gunicorn/Uvicorn, autoscaled 2→10 on CPU)
                  (private subnets)        │
                                           ├─► RDS PostgreSQL (Multi-AZ, encrypted)
                                           ├─► ElastiCache Redis (replication group)
                                           └─► Qdrant (ECS service + EFS, via Cloud Map DNS)
Secrets Manager ─► task secrets   ECR ─► images   CloudWatch ─► logs+insights
```

| File | Resources |
|---|---|
| `versions.tf` | Terraform + AWS provider, default tags, (S3 backend stub) |
| `variables.tf` / `terraform.tfvars.example` | inputs incl. sensitive `db_password`, `jwt_secret` |
| `network.tf` | VPC, 2 public + 2 private subnets, IGW, NAT, route tables |
| `security_groups.tf` | ALB, ECS, RDS, Redis, Qdrant SGs (least-privilege chaining) |
| `ecr.tf` | image repo + lifecycle policy |
| `iam.tf` | task execution role (+ secrets read), task role |
| `secrets.tf` | Secrets Manager secret (JSON of runtime secrets) |
| `cloudwatch.tf` | log groups (api, qdrant) |
| `rds.tf` | PostgreSQL 16, Multi-AZ, encrypted, backups |
| `elasticache.tf` | Redis 7 replication group, auto-failover |
| `qdrant.tf` | EFS + ECS Fargate service + Cloud Map `qdrant.god-mode.local` |
| `alb.tf` | ALB, target group (`/health`), HTTP listener |
| `ecs.tf` | cluster, task def (env + Secrets Manager secrets), service, CPU autoscaling |
| `cloudfront_s3.tf` | private S3 + CloudFront (OAC) |
| `route53.tf` | optional ALB alias record |
| `outputs.tf` | ALB DNS, ECR URL, RDS/Redis endpoints, CloudFront domain |

## Deploy

```bash
cd deployment/aws/terraform
cp terraform.tfvars.example terraform.tfvars   # fill in secrets
terraform init
terraform plan
terraform apply

# Build & push the first image to the new ECR repo:
aws ecr get-login-password --region us-east-1 | docker login --username AWS --password-stdin <ECR_URL>
docker build -f ../../../docker/Dockerfile -t <ECR_URL>:latest ../../..
docker push <ECR_URL>:latest

# Force a new deployment to pick it up:
aws ecs update-service --cluster god-mode-ai-cluster --service god-mode-ai-api --force-new-deployment
```

The API is then reachable at the `alb_dns_name` output (put it behind Route53 + ACM for HTTPS).

## CI/CD

`.github/workflows/deploy.yml` runs on push to `main`:
1. **test** — installs deps, runs `pytest backend/tests/unit`.
2. **build-and-deploy** — assumes an AWS role via OIDC, builds the Docker image, pushes to ECR,
   renders a new task definition with the new image, and deploys to ECS with
   wait-for-stability (deployment circuit breaker auto-rolls back on failure).

Required GitHub secret: `AWS_DEPLOY_ROLE_ARN` (an IAM role trusting the GitHub OIDC provider).

## Notes / production hardening

- Add an ACM cert + HTTPS listener (443) and redirect 80→443; wire `domain_name` + `route53_zone_id`.
- Move Terraform state to the S3 backend (stub in `versions.tf`) with DynamoDB locking.
- `USE_IN_MEMORY_BACKENDS=false` so the app uses the real RDS/Redis/Qdrant adapters (Phase 7).
- Validated structurally here (Terraform/AWS not available in the build sandbox); run
  `terraform init && terraform validate` in your environment before applying.
