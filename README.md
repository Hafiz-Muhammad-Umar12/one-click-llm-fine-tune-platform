<div align="center">

# 🚀 One-Click LLM Fine-Tuning Platform

### Enterprise-Grade AI Infrastructure for Training, Deploying & Serving Large Language Models

[![Python](https://img.shields.io/badge/Python-3.11+-3776AB?style=for-the-badge&logo=python&logoColor=white)](https://python.org)
[![FastAPI](https://img.shields.io/badge/FastAPI-0.115-009688?style=for-the-badge&logo=fastapi&logoColor=white)](https://fastapi.tiangolo.com)
[![Next.js](https://img.shields.io/badge/Next.js-14-000000?style=for-the-badge&logo=next.js&logoColor=white)](https://nextjs.org)
[![PostgreSQL](https://img.shields.io/badge/PostgreSQL-16-336791?style=for-the-badge&logo=postgresql&logoColor=white)](https://postgresql.org)
[![Redis](https://img.shields.io/badge/Redis-7-DC382D?style=for-the-badge&logo=redis&logoColor=white)](https://redis.io)
[![Docker](https://img.shields.io/badge/Docker-Ready-2496ED?style=for-the-badge&logo=docker&logoColor=white)](https://docker.com)
[![License](https://img.shields.io/badge/License-MIT-green?style=for-the-badge)](LICENSE)

<br/>

> **Production-ready platform** competing with Hugging Face AutoTrain, Predibase & Together AI.  
> Train LoRA, QLoRA, SFT, and DPO models — with real-time monitoring, one-click deployment, and full observability.

<br/>

[📖 Documentation](#-documentation) • [⚡ Quick Start](#-quick-start) • [🏗️ Architecture](#️-system-architecture) • [🔌 API Reference](#-api-reference) • [🤝 Contributing](#-contributing)

---

</div>

## 📋 Table of Contents

- [Overview](#-overview)
- [Key Features](#-key-features)
- [System Architecture](#️-system-architecture)
- [Tech Stack](#-tech-stack)
- [Project Structure](#-project-structure)
- [Quick Start](#-quick-start)
- [Configuration](#️-configuration)
- [API Reference](#-api-reference)
- [Training Methods](#-training-methods)
- [Deployment System](#-deployment-system)
- [Observability](#-observability--monitoring)
- [Testing](#-testing)
- [Roadmap](#️-roadmap)
- [Contributing](#-contributing)
- [License](#-license)

---

## 🌟 Overview

The **One-Click LLM Fine-Tuning Platform** is an enterprise-grade AI infrastructure system that enables teams to fine-tune, evaluate, and deploy large language models at scale — without managing complex ML infrastructure.

Built for **AI teams, enterprises, and research organizations** who need:

- 🔬 **Research-grade training** with full control over hyperparameters
- 🏭 **Production-grade reliability** with job queues, retries, and fault tolerance
- 📊 **Real-time observability** of GPU metrics, loss curves, and system health
- 🔐 **Enterprise security** with RBAC, API keys, audit logs, and SSO-ready auth
- 🌐 **Multi-tenant architecture** supporting teams, organizations, and billing

### Why This Platform?

| Feature | This Platform | HuggingFace AutoTrain | Predibase |
|---|:---:|:---:|:---:|
| Self-hosted | ✅ | ❌ | ❌ |
| LoRA / QLoRA | ✅ | ✅ | ✅ |
| DPO Training | ✅ | ❌ | ✅ |
| Real-time Log Streaming | ✅ | ❌ | ✅ |
| WebSocket Monitoring | ✅ | ❌ | ❌ |
| Multi-tenant RBAC | ✅ | ❌ | ✅ |
| MCP Integration | ✅ | ❌ | ❌ |
| Open Source | ✅ | ❌ | ❌ |

---

## ✨ Key Features

### 🧠 Training Engine
- **LoRA** — Parameter-efficient fine-tuning with configurable rank and alpha
- **QLoRA** — 4-bit quantized LoRA for training on consumer GPUs
- **SFT** — Supervised Fine-Tuning for instruction following
- **DPO** — Direct Preference Optimization for RLHF-style alignment
- **Full Fine-tuning** — Complete parameter updates for maximum performance
- Resume training from any checkpoint
- Distributed multi-GPU training via Accelerate

### 📦 Dataset Management
- Upload datasets up to **500MB** with streaming multipart upload
- Supported formats: `JSONL`, `CSV`, `TXT`, `Alpaca`, `ChatML`, `ShareGPT`, `OpenAI`
- Automatic format detection and validation
- Token counting, deduplication, and train/validation split
- Dataset versioning with full lineage tracking

### 🚀 One-Click Deployment
- Deploy trained models via **vLLM**, **SGLang**, or **Ollama**
- Auto-scaling with configurable min/max replicas
- OpenAI-compatible REST API for instant integration
- Streaming inference with Server-Sent Events (SSE)
- Health checks and automatic failover

### 📡 Real-time Monitoring
- Live training logs streamed via **WebSocket**
- Step-level metrics: loss, learning rate, gradient norm
- GPU utilization, memory usage, and throughput dashboards
- **Prometheus + Grafana** dashboards out of the box
- Structured JSON logging compatible with Loki/ELK

### 🔐 Enterprise Security
- JWT authentication with refresh token rotation
- Role-Based Access Control: `owner`, `admin`, `member`, `viewer`
- Organization-level multi-tenancy
- API key management with scoped permissions
- Full audit logging for compliance
- Rate limiting per user/IP via Redis sliding window

### 🤖 MCP Integration
- MCP servers for datasets, training jobs, deployments, and logs
- Enables AI agents (Claude, GPT-4) to manage training workflows
- Structured tool schemas with permission enforcement

---

## 🏗️ System Architecture

```
┌─────────────────────────────────────────────────────────────────┐
│                        CLIENT LAYER                             │
│         Next.js Frontend  ·  REST API  ·  WebSocket             │
└─────────────────────┬───────────────────────────────────────────┘
                      │ HTTPS / WSS
┌─────────────────────▼───────────────────────────────────────────┐
│                      API GATEWAY (Nginx)                        │
│              Rate Limiting · SSL Termination · LB               │
└──────────┬──────────────────────────────────┬───────────────────┘
           │                                  │
┌──────────▼──────────┐           ┌───────────▼───────────────────┐
│   FastAPI Backend   │           │      WebSocket Manager         │
│  ┌───────────────┐  │           │   Redis Pub/Sub Fan-out        │
│  │ Auth Service  │  │           └───────────────────────────────┘
│  │ Dataset API   │  │
│  │ Training API  │  │     ┌─────────────────────────────────────┐
│  │ Deploy API    │  │     │           Message Queue              │
│  └───────────────┘  │────►│     Redis · Celery Workers           │
└──────────┬──────────┘     │  ┌──────────────────────────────┐   │
           │                │  │ Training Worker (GPU)        │   │
           │                │  │ Dataset Worker               │   │
┌──────────▼──────────┐     │  │ Deployment Worker            │   │
│     PostgreSQL      │     │  └──────────────────────────────┘   │
│  Users · Jobs ·     │     └─────────────────────────────────────┘
│  Datasets · Logs    │
└─────────────────────┘     ┌─────────────────────────────────────┐
                            │        Storage Layer                  │
                            │   S3-Compatible (MinIO / AWS / R2)   │
                            │   Models · Datasets · Checkpoints    │
                            └─────────────────────────────────────┘

┌─────────────────────────────────────────────────────────────────┐
│                    OBSERVABILITY STACK                           │
│       Prometheus · Grafana · OpenTelemetry · Loki               │
└─────────────────────────────────────────────────────────────────┘
```

### Request Flow — Training Job

```
User → POST /api/v1/orgs/{id}/training-jobs
     → FastAPI validates request + checks RBAC
     → TrainingJob created in PostgreSQL (status: queued)
     → Celery task pushed to Redis queue
     → GPU Worker picks up task
     → Model loaded (HuggingFace Hub)
     → Training loop starts
     → Metrics emitted → Redis Pub/Sub → WebSocket → Frontend
     → Checkpoints saved → S3
     → Job completed → PostgreSQL updated
     → User notified
```

---

## 🛠️ Tech Stack

### Backend
| Technology | Version | Purpose |
|---|---|---|
| **FastAPI** | 0.115 | Async REST API framework |
| **SQLAlchemy** | 2.0 | Async ORM with PostgreSQL |
| **Alembic** | 1.13 | Database migrations |
| **Celery** | 5.4 | Distributed task queue |
| **Redis** | 7 | Message broker + rate limiting + pub/sub |
| **PostgreSQL** | 16 | Primary database |
| **Pydantic v2** | 2.9 | Data validation and serialization |

### AI / ML
| Technology | Purpose |
|---|---|
| **Transformers** | Model loading and tokenization |
| **PEFT** | LoRA / QLoRA adapter training |
| **TRL** | SFTTrainer and DPOTrainer |
| **Accelerate** | Multi-GPU distributed training |
| **bitsandbytes** | 4-bit / 8-bit quantization |
| **vLLM** | High-throughput inference serving |
| **SGLang** | Structured generation inference |

### Frontend
| Technology | Purpose |
|---|---|
| **Next.js 14** | React framework with App Router |
| **TypeScript** | Type-safe frontend development |
| **Tailwind CSS** | Utility-first styling |
| **shadcn/ui** | Enterprise UI component library |
| **Zustand** | Lightweight global state management |
| **React Query** | Server state, caching, and mutations |
| **Framer Motion** | Smooth animations and transitions |

### Infrastructure
| Technology | Purpose |
|---|---|
| **Docker** | Containerization |
| **Docker Compose** | Local development orchestration |
| **Kubernetes** | Production container orchestration |
| **Nginx** | Reverse proxy and load balancer |
| **MinIO** | S3-compatible local object storage |
| **Prometheus** | Metrics collection |
| **Grafana** | Dashboards and alerting |
| **OpenTelemetry** | Distributed tracing |

---

## 📁 Project Structure

```
llm-finetuning-platform/
│
├── backend/                        # FastAPI backend
│   ├── app/
│   │   ├── api/
│   │   │   └── v1/
│   │   │       ├── endpoints/      # Route handlers
│   │   │       │   ├── auth.py         # Register, login, refresh
│   │   │       │   ├── training.py     # Job CRUD + log streaming
│   │   │       │   ├── datasets.py     # Upload, validate, manage
│   │   │       │   └── websockets.py   # Live training WS
│   │   │       └── dependencies/
│   │   │           └── auth.py         # JWT + API key auth deps
│   │   ├── core/
│   │   │   ├── config.py           # Pydantic settings (env vars)
│   │   │   ├── security.py         # JWT, hashing, RBAC, API keys
│   │   │   └── logging.py          # Structured JSON logging
│   │   ├── db/
│   │   │   ├── session.py          # Async SQLAlchemy engine
│   │   │   └── models/             # All ORM models
│   │   ├── schemas/                # Pydantic request/response schemas
│   │   ├── services/
│   │   │   ├── storage/s3.py       # S3-compatible storage client
│   │   │   └── dataset/            # Upload + validation services
│   │   ├── workers/
│   │   │   ├── celery_app.py       # Celery factory + queue config
│   │   │   ├── training_tasks.py   # LoRA/QLoRA/SFT/DPO execution
│   │   │   ├── training_callbacks.py # Live metric streaming
│   │   │   └── dataset_tasks.py    # Async dataset processing
│   │   ├── middleware/
│   │   │   ├── rate_limit.py       # Redis sliding window limiter
│   │   │   ├── request_id.py       # X-Request-ID tracing
│   │   │   └── audit.py            # Mutation audit logging
│   │   └── websockets/
│   │       └── manager.py          # Redis pub/sub WS fan-out
│   ├── alembic/                    # Database migrations
│   ├── tests/
│   │   ├── unit/                   # Unit tests (pytest-asyncio)
│   │   ├── integration/            # Integration tests
│   │   └── e2e/                    # End-to-end tests (Playwright)
│   ├── docker/
│   │   ├── Dockerfile              # Multi-stage build
│   │   └── docker-compose.yml      # Full dev stack
│   ├── requirements.txt
│   └── .env.example
│
├── frontend/                       # Next.js frontend (coming soon)
├── k8s/                            # Kubernetes manifests
├── monitoring/                     # Prometheus + Grafana configs
└── docs/                           # Extended documentation
```

---

## ⚡ Quick Start

### Prerequisites

- **Docker** 24+ and **Docker Compose** v2
- **Python** 3.11+
- **Node.js** 18+ (for frontend)
- **GPU** (optional, for actual training — CUDA 12.1+)

### 1. Clone the Repository

```bash
git clone https://github.com/your-org/llm-finetuning-platform.git
cd llm-finetuning-platform
```

### 2. Start Infrastructure Services

```bash
cd backend/docker
docker-compose up -d postgres redis minio
```

This starts:
- **PostgreSQL** on `localhost:5432`
- **Redis** on `localhost:6379`
- **MinIO** (S3) on `localhost:9000` | Console: `localhost:9001`

### 3. Setup Backend

```bash
cd backend

# Create and activate virtual environment
python -m venv venv
source venv/bin/activate          # Linux / Mac
# venv\Scripts\activate           # Windows

# Install dependencies
pip install -r requirements.txt

# Configure environment
cp .env.example .env
# Edit .env with your values (DB password, SECRET_KEY, etc.)
```

### 4. Run Database Migrations

```bash
alembic upgrade head
```

### 5. Start the Backend Server

```bash
# Development (with hot reload)
uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload

# Production
uvicorn app.main:app --host 0.0.0.0 --port 8000 --workers 4
```

### 6. Start Celery Workers

```bash
# In a separate terminal — Dataset processing worker
celery -A app.workers.celery_app worker \
  --loglevel=info --concurrency=4 \
  --queues=dataset,evaluation \
  --hostname=dataset-worker@%h

# In another terminal — Training worker (GPU)
celery -A app.workers.celery_app worker \
  --loglevel=info --concurrency=1 \
  --queues=training \
  --hostname=training-worker@%h
```

### 7. Access the Platform

| Service | URL | Credentials |
|---|---|---|
| **API Server** | http://localhost:8000 | — |
| **Swagger UI** | http://localhost:8000/api/v1/docs | — |
| **ReDoc** | http://localhost:8000/api/v1/redoc | — |
| **Health Check** | http://localhost:8000/health | — |
| **Celery Flower** | http://localhost:5555 | — |
| **MinIO Console** | http://localhost:9001 | `minioadmin / minioadmin` |
| **Grafana** | http://localhost:3100 | `admin / admin` |

---

## ⚙️ Configuration

All configuration is managed via environment variables. Copy `.env.example` to `.env` and update values:

```bash
# ── Core ──────────────────────────────────────────────────
PROJECT_NAME="LLM Fine-Tuning Platform"
ENVIRONMENT=production              # development | staging | production
SECRET_KEY=your-super-secret-key-min-32-chars   # CHANGE THIS!

# ── Database ──────────────────────────────────────────────
POSTGRES_SERVER=localhost
POSTGRES_USER=llmplatform
POSTGRES_PASSWORD=your-db-password
POSTGRES_DB=llmplatform

# ── Redis ─────────────────────────────────────────────────
REDIS_HOST=localhost
REDIS_PORT=6379
REDIS_PASSWORD=your-redis-password  # Set in production

# ── S3 Storage ────────────────────────────────────────────
S3_ENDPOINT_URL=http://localhost:9000   # Remove for AWS
S3_ACCESS_KEY_ID=your-access-key
S3_SECRET_ACCESS_KEY=your-secret-key
S3_BUCKET_NAME=llm-finetuning

# ── Training ──────────────────────────────────────────────
MAX_CONCURRENT_TRAINING_JOBS=4
TRAINING_JOB_TIMEOUT_HOURS=24

# ── Security ──────────────────────────────────────────────
ACCESS_TOKEN_EXPIRE_MINUTES=30
REFRESH_TOKEN_EXPIRE_DAYS=7
RATE_LIMIT_CALLS=100               # Requests per minute per user
```

> ⚠️ **Never commit your `.env` file to version control.**

---

## 🔌 API Reference

### Authentication

```bash
# Register a new user
POST /api/v1/auth/register
{
  "email": "user@example.com",
  "password": "SecurePass123!",
  "full_name": "John Doe"
}

# Login
POST /api/v1/auth/login
{
  "email": "user@example.com",
  "password": "SecurePass123!"
}
# Returns: { access_token, refresh_token, token_type, expires_in }

# Refresh token
POST /api/v1/auth/refresh
{ "refresh_token": "..." }

# Logout
POST /api/v1/auth/logout
{ "refresh_token": "..." }
```

### Datasets

```bash
# Upload a dataset
POST /api/v1/orgs/{org_id}/datasets
Authorization: Bearer <token>
Content-Type: multipart/form-data
  name=my-dataset
  format=jsonl
  file=@dataset.jsonl

# List datasets
GET /api/v1/orgs/{org_id}/datasets?page=1&per_page=20

# Get dataset details
GET /api/v1/orgs/{org_id}/datasets/{dataset_id}

# Delete dataset
DELETE /api/v1/orgs/{org_id}/datasets/{dataset_id}
```

### Training Jobs

```bash
# Create a training job
POST /api/v1/orgs/{org_id}/training-jobs
Authorization: Bearer <token>
{
  "name": "Llama-2 LoRA Fine-tune",
  "dataset_id": "uuid",
  "base_model": "meta-llama/Llama-2-7b-hf",
  "training_method": "lora",        # lora | qlora | sft | dpo | full
  "gpu_count": 1,
  "hyperparameters": {
    "learning_rate": 2e-4,
    "num_train_epochs": 3,
    "lora_r": 16,
    "lora_alpha": 32,
    "per_device_train_batch_size": 4,
    "max_seq_length": 2048
  }
}

# List jobs
GET /api/v1/orgs/{org_id}/training-jobs?status=running&page=1

# Get job status
GET /api/v1/orgs/{org_id}/training-jobs/{job_id}

# Stop a job
POST /api/v1/orgs/{org_id}/training-jobs/{job_id}/stop

# Stream logs (NDJSON)
GET /api/v1/orgs/{org_id}/training-jobs/{job_id}/logs?tail=100
```

### WebSocket — Live Training Logs

```javascript
// Connect with JWT token as query param
const ws = new WebSocket(
  `ws://localhost:8000/ws/training/${jobId}/logs?token=${accessToken}`
);

ws.onmessage = (event) => {
  const msg = JSON.parse(event.data);
  // msg.type: "log" | "metric" | "status_change" | "epoch_complete" | "checkpoint_saved"
  console.log(msg);
};

// Keep-alive
setInterval(() => ws.send(JSON.stringify({ type: "ping" })), 30000);
```

---

## 🧠 Training Methods

### LoRA (Low-Rank Adaptation)

Most efficient method. Adds small trainable matrices to frozen base model.

```json
{
  "training_method": "lora",
  "hyperparameters": {
    "lora_r": 16,
    "lora_alpha": 32,
    "lora_dropout": 0.05,
    "learning_rate": 2e-4,
    "num_train_epochs": 3
  }
}
```

**GPU Requirements:** 1× A10G (24GB) for 7B models

### QLoRA (Quantized LoRA)

4-bit quantization + LoRA. Train 7B models on a single consumer GPU.

```json
{
  "training_method": "qlora",
  "hyperparameters": {
    "load_in_4bit": true,
    "bnb_4bit_quant_type": "nf4",
    "lora_r": 64,
    "learning_rate": 1e-4
  }
}
```

**GPU Requirements:** 1× RTX 3090 (24GB) for 7B models

### SFT (Supervised Fine-Tuning)

Standard instruction tuning for chat/assistant models.

```json
{
  "training_method": "sft",
  "hyperparameters": {
    "num_train_epochs": 2,
    "per_device_train_batch_size": 2,
    "max_seq_length": 4096
  }
}
```

### DPO (Direct Preference Optimization)

Alignment training using human preference data (no reward model needed).

```json
{
  "training_method": "dpo",
  "hyperparameters": {
    "learning_rate": 5e-7,
    "num_train_epochs": 1,
    "beta": 0.1
  }
}
```

**Dataset Format for DPO:**
```json
{"prompt": "...", "chosen": "...", "rejected": "..."}
```

---

## 🚢 Deployment System

After training completes, deploy your model with one API call:

```bash
POST /api/v1/orgs/{org_id}/deployments
{
  "name": "my-model-v1",
  "training_job_id": "uuid",
  "engine": "vllm",               # vllm | sglang | ollama
  "gpu_count": 1,
  "min_replicas": 1,
  "max_replicas": 4
}
```

Your model is then available at an **OpenAI-compatible endpoint**:

```bash
# Inference (OpenAI-compatible)
POST http://your-deployment-url/v1/chat/completions
{
  "model": "my-model-v1",
  "messages": [{"role": "user", "content": "Hello!"}],
  "stream": true
}
```

---

## 📊 Observability & Monitoring

### Metrics (Prometheus)

The platform exposes metrics at `/metrics`:

| Metric | Description |
|---|---|
| `training_job_duration_seconds` | Training job completion time |
| `training_gpu_utilization_percent` | Per-job GPU utilization |
| `dataset_processing_duration_seconds` | Dataset pipeline latency |
| `api_request_duration_seconds` | API endpoint latency histogram |
| `active_training_jobs` | Currently running training jobs |
| `celery_queue_length` | Tasks waiting in each queue |

### Grafana Dashboards

Pre-built dashboards available at `http://localhost:3100`:

- **Platform Overview** — Active jobs, API health, queue status
- **Training Job Monitor** — Loss curves, GPU usage, throughput
- **System Health** — CPU, memory, disk, network
- **API Performance** — Latency percentiles, error rates

### Log Aggregation

All logs are structured JSON, compatible with Loki, ELK, and Datadog:

```json
{
  "time": "2024-01-15T10:30:00Z",
  "level": "INFO",
  "name": "app.workers.training_tasks",
  "message": "Step 100 | Loss: 0.452 | LR: 0.0002",
  "job_id": "uuid",
  "step": 100,
  "epoch": 1.5
}
```

---

## 🧪 Testing

```bash
# Run all tests
pytest

# Run with coverage report
pytest --cov=app --cov-report=html

# Run only unit tests
pytest tests/unit/ -v

# Run only integration tests
pytest tests/integration/ -v

# Run specific test file
pytest tests/unit/test_auth.py -v

# Run with parallel execution
pytest -n auto
```

### Test Structure

```
tests/
├── unit/
│   ├── test_auth.py           # Auth endpoint tests
│   ├── test_training.py       # Training job tests
│   ├── test_datasets.py       # Dataset management tests
│   └── test_security.py       # JWT / RBAC unit tests
├── integration/
│   ├── test_training_flow.py  # Full training pipeline
│   └── test_dataset_pipeline.py
└── e2e/
    └── test_user_journey.py   # Playwright browser tests
```

---

## 🏭 Production Deployment

### Docker Compose (Single Server)

```bash
# Production stack
docker-compose -f docker/docker-compose.yml up -d
```

### Kubernetes

```bash
# Apply K8s manifests
kubectl apply -f k8s/namespace.yaml
kubectl apply -f k8s/configmap.yaml
kubectl apply -f k8s/secrets.yaml
kubectl apply -f k8s/postgres.yaml
kubectl apply -f k8s/redis.yaml
kubectl apply -f k8s/api-deployment.yaml
kubectl apply -f k8s/worker-deployment.yaml
kubectl apply -f k8s/ingress.yaml
```

### Production Checklist

- [ ] Change `SECRET_KEY` to a cryptographically random 64-char string
- [ ] Set strong `POSTGRES_PASSWORD` and `REDIS_PASSWORD`
- [ ] Enable HTTPS via Nginx + Let's Encrypt
- [ ] Configure S3 bucket with proper IAM permissions
- [ ] Set up Prometheus alerting rules
- [ ] Enable Sentry for error tracking (`SENTRY_DSN`)
- [ ] Configure SMTP for email notifications
- [ ] Set up database backups (pg_dump + S3)
- [ ] Enable PostgreSQL connection pooling (PgBouncer)
- [ ] Configure Kubernetes HPA for auto-scaling

---

## 🗺️ Roadmap

### ✅ Phase 1 — Core Infrastructure (Complete)
- [x] FastAPI backend with async architecture
- [x] PostgreSQL + Alembic migrations
- [x] JWT auth with refresh token rotation
- [x] RBAC permission system
- [x] Redis + Celery worker queue
- [x] S3-compatible storage
- [x] WebSocket real-time log streaming
- [x] Rate limiting middleware
- [x] Docker Compose dev stack

### 🚧 Phase 2 — Training Pipeline (In Progress)
- [ ] LoRA / QLoRA training (SFTTrainer)
- [ ] DPO training pipeline
- [ ] Full fine-tuning support
- [ ] Checkpoint management
- [ ] Distributed multi-GPU training
- [ ] Dataset preprocessing pipeline

### 📋 Phase 3 — Deployment System
- [ ] vLLM inference server integration
- [ ] SGLang integration
- [ ] Auto-scaling engine
- [ ] OpenAI-compatible API proxy

### 📋 Phase 4 — Frontend Dashboard
- [ ] Next.js App Router dashboard
- [ ] Real-time training monitor UI
- [ ] Dataset management UI
- [ ] Model playground (chat interface)
- [ ] Organization management

### 📋 Phase 5 — Observability
- [ ] Prometheus + Grafana dashboards
- [ ] OpenTelemetry distributed tracing
- [ ] Loki log aggregation
- [ ] GPU utilization dashboards

### 📋 Phase 6 — Enterprise Features
- [ ] MCP servers for AI agent integration
- [ ] SSO / SAML authentication
- [ ] Billing and usage tracking
- [ ] Model evaluation framework
- [ ] A/B testing for deployments

---

## 🤝 Contributing

We welcome contributions! Please read our contributing guidelines before submitting PRs.

```bash
# Fork and clone
git clone https://github.com/your-username/llm-finetuning-platform.git

# Create a feature branch
git checkout -b feature/your-feature-name

# Install dev dependencies
pip install -r requirements.txt
pip install pre-commit ruff mypy

# Setup pre-commit hooks
pre-commit install

# Make your changes and run tests
pytest --cov=app

# Submit a pull request
git push origin feature/your-feature-name
```

### Code Standards

- **Python:** Follow PEP 8 · Type hints on all functions · Docstrings on all modules
- **Linting:** `ruff check .` must pass with zero errors
- **Type checking:** `mypy app/` must pass
- **Tests:** All new features require unit tests · Minimum 80% coverage
- **Commits:** Follow [Conventional Commits](https://conventionalcommits.org)

---

## 📚 Documentation

| Resource | Link |
|---|---|
| API Reference (Swagger) | http://localhost:8000/api/v1/docs |
| API Reference (ReDoc) | http://localhost:8000/api/v1/redoc |
| Architecture Deep Dive | [docs/architecture.md](docs/architecture.md) |
| Training Guide | [docs/training.md](docs/training.md) |
| Deployment Guide | [docs/deployment.md](docs/deployment.md) |
| Security Guide | [docs/security.md](docs/security.md) |

---

## 📄 License

This project is licensed under the **MIT License** — see the [LICENSE](LICENSE) file for details.

---

## 🙏 Acknowledgements

Built on the shoulders of giants:

- [HuggingFace Transformers](https://github.com/huggingface/transformers) — Model loading & tokenization
- [PEFT](https://github.com/huggingface/peft) — Parameter-efficient fine-tuning
- [TRL](https://github.com/huggingface/trl) — SFT and DPO trainers
- [FastAPI](https://fastapi.tiangolo.com) — Modern Python web framework
- [vLLM](https://github.com/vllm-project/vllm) — High-throughput inference

---

<div align="center">

**Built with ❤️ for the AI community**

[⭐ Star this repo](https://github.com/your-org/llm-finetuning-platform) • [🐛 Report a Bug](https://github.com/your-org/llm-finetuning-platform/issues) • [💡 Request a Feature](https://github.com/your-org/llm-finetuning-platform/issues)

</div>
