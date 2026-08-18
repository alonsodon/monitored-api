# Monitored API

A production-grade REST API for task management, built to demonstrate modern
Python backend engineering end-to-end — from local development to a fully
automated, self-healing deployment on AWS.

**Stack:** FastAPI · PostgreSQL · SQLAlchemy · Alembic · Docker · GitHub Actions · Terraform (AWS) · Prometheus · Grafana

## Architecture

```
GitHub Actions (CI/CD)
  ├── test job:        pytest + coverage gate (fails the build if <70%)
  └── build-push job:  (main only) Docker build → push to ECR via OIDC (no long-lived AWS keys)
        │
        ▼
AWS (Terraform-managed, two isolated states)
  ├── infra/bootstrap/   S3 state bucket + DynamoDB lock + OIDC role + ECR   → permanent
  └── infra/             VPC (public/private subnets) + RDS + EC2           → ephemeral, destroy/recreate freely
        │
        EC2 (public subnet)
          └── user_data: docker pull → alembic upgrade head (throwaway container) → run
        │
        RDS PostgreSQL (private subnet, reachable ONLY from the EC2's security group)

Prometheus ← scrapes GET /metrics every 15s
Grafana    ← dashboards: request rate, P95 latency, business metrics (tasks created/completed)
```

## Stack

| Layer          | Technology                        | Why                                                                                                      |
| -------------- | --------------------------------- | -------------------------------------------------------------------------------------------------------- |
| API            | FastAPI + Pydantic v2             | Automatic request validation, generated OpenAPI docs, native dependency injection                        |
| Database       | PostgreSQL + SQLAlchemy + Alembic | Versioned, reversible schema migrations; same ORM code across SQLite (tests) and Postgres (dev/prod)     |
| Container      | Docker multi-stage                | Builder stage compiles dependencies; production stage is ~80% smaller, runs as non-root                  |
| CI             | GitHub Actions                    | Every PR runs the full test suite with a coverage gate before merge is allowed                           |
| CD             | GitHub Actions + OIDC → ECR       | Short-lived AWS credentials scoped to this repo only — zero secrets stored in GitHub                     |
| Infrastructure | Terraform                         | Entire AWS footprint as code, split into permanent (bootstrap) and disposable (workload) state           |
| Observability  | Prometheus + Grafana              | Technical metrics (request rate, P95 latency, error rate) and business metrics (tasks created/completed) |

## Project structure

```
app/
├── main.py            # FastAPI app, global middleware, health/metrics endpoints
├── database.py         # engine, SessionLocal, get_db, DB dependency alias
├── models.py            # SQLAlchemy models
├── schemas.py             # Pydantic schemas (Create / Update / Response)
├── metrics.py               # Prometheus counters and histograms
├── services.py                 # external notification integration (mocked in tests)
└── routers/
    └── tasks.py                    # CRUD endpoints for the task resource
tests/                                  # pytest suite: fixtures, isolated in-memory DB, mocks
alembic/versions/                          # versioned schema migrations (2 revisions)
infra/
├── main.tf, rds.tf, ec2.tf, ...              # VPC, RDS, EC2 — recreated/destroyed freely
└── bootstrap/                                  # S3 state bucket, DynamoDB lock, OIDC role, ECR — permanent
monitoring/prometheus.yml                          # scrape config
scripts/                                             # AWS cost/resource audit helpers
docker-compose.yml                                     # local stack: api + db + prometheus + grafana
Dockerfile                                               # multi-stage production build
```

## Run locally

```bash
cp .env.example .env                 # fill in local secrets
docker compose up -d                 # api + db + prometheus + grafana
docker compose exec api alembic upgrade head
curl http://localhost:8000/health    # {"status":"ok"}
open http://localhost:3000           # Grafana (admin/admin) — add datasource http://prometheus:9090
pytest tests/ --cov=app              # 20 tests, ~94% coverage
```

## Deploy to AWS

```bash
# one-time bootstrap: creates the S3 state bucket, DynamoDB lock table,
# the OIDC role GitHub Actions will assume, and the ECR repository
cd infra/bootstrap && terraform init && terraform apply

# migrate the app's Terraform state to the S3 backend just created
cd .. && terraform init

# push to main → CI builds the image and pushes it to ECR
# provision the VPC, RDS and EC2 — the EC2 self-deploys on boot:
# pull the image → run migrations → start serving traffic
terraform apply

# a few minutes later:
curl http://$(terraform output -raw app_public_ip):8000/health
```

To tear down the practice environment without touching CI/CD or the state backend:

```bash
cd infra && terraform destroy   # bootstrap/ is untouched (protected by prevent_destroy)
```

## Key decisions

- **FastAPI over Flask** — automatic request validation and OpenAPI docs replace hand-written checks; native dependency injection makes the app trivially testable.
- **Three-schema pattern** (`Create` / `Update` / `Response`) — decouples what a client sends, what's persisted, and what's exposed. `id` and `created_at` are server-assigned and never accepted from the client.
- **Terraform state split into bootstrap vs. workload** — the S3 bucket, DynamoDB lock table, OIDC role, and ECR repository live in a separate, `prevent_destroy`-protected configuration from the VPC/RDS/EC2. The disposable practice infrastructure can be destroyed and recreated daily without any risk to the CI/CD identity or the Terraform state itself.
- **OIDC over static AWS access keys** — GitHub Actions authenticates using short-lived, repository-scoped tokens; no credentials are stored as GitHub secrets.
- **Migrations run automatically on deploy** — the EC2's `user_data` runs `alembic upgrade head` in a throwaway container _before_ starting the app, so the schema is guaranteed current the moment the app begins serving traffic — no manual step required.
- **The same ORM code runs against SQLite (tests) and PostgreSQL (dev/prod)** — tests run fully isolated and in-memory via dependency overrides (`app.dependency_overrides[get_db]`), with zero external services required to run the suite.
- **Metric label cardinality is controlled** — HTTP metrics key off the route _template_ (`/tasks/{task_id}`) rather than the resolved path, preventing unbounded label growth as the number of tasks increases.
- **Dependencies are locked with pip-tools** — `requirements.in`/`.txt` separate declared intent from the fully resolved dependency tree; production and dev dependencies are locked independently, keeping test tooling out of the production image entirely.

## Testing

20 tests, ~94% coverage: integration tests against an isolated in-memory SQLite database via FastAPI's `TestClient`, boundary-value tests for validation limits (`parametrize`), and mocked external HTTP calls for the notification service — no external services required to run the suite.

## Cost awareness

`scripts/check_aws.sh` and `scripts/check_after_destroy.sh` audit live AWS resources directly via the CLI (rather than relying on Cost Explorer, which lags up to 24h) to confirm nothing is left running between practice sessions.

## License

MIT
