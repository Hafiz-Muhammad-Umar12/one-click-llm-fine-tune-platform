# Backend API - One-Click AI Platform

The Backend API serves as the central control plane for the One-Click AI Platform, orchestrating datasets, training jobs, model versioning, and deployment endpoints.

## Tech Stack
- **Framework:** FastAPI
- **Database:** PostgreSQL (asyncpg) with SQLAlchemy 2.0
- **Cache & Pub/Sub:** Redis
- **Task Queue:** Celery
- **Observability:** Prometheus, OpenTelemetry
- **Rate Limiting:** fastapi-limiter

## Key Modules

### 1. Training Engine (`src/training/`)
Handles the orchestration of machine learning training jobs across distributed GPU workers. Integrates with Celery for background processing.

### 2. Model Registry & Deployments (`src/deployment/`)
Manages `RegisteredModel`, `ModelVersion`, and `DeploymentEndpoint` entities. It handles autoscaling logic, VRAM-aware GPU scheduling, and zero-downtime rollbacks via immutable `DeploymentRevisions`.

### 3. Datasets (`src/datasets/`)
Manages S3 integration for robust, direct-to-storage uploads of training data (JSONL, CSV).

### 4. Real-time (`src/websocket/`)
Websocket managers handle the streaming of training logs and real-time generation tokens back to the client via Redis Pub/Sub.

## Observability & Compliance
- **Metrics:** `/metrics` endpoint is exposed for Prometheus scraping.
- **Rate Limiting:** Public inference endpoints are protected by Redis rate limiting.
- **Audit Logs:** All state-mutating requests (`POST`, `PUT`, `DELETE`) are logged to the `audit_log` table by `AuditMiddleware` to ensure enterprise compliance.
- **Tenant Isolation:** Enforced via organizational API Keys and strict Row-Level Security checks.

## Getting Started

```bash
# Setup virtual environment
python -m venv venv
source venv/bin/activate

# Install dependencies
pip install -e .[test]

# Run migrations
alembic upgrade head

# Run server
uvicorn src.main:app --reload
```
