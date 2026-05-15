# One-Click AI Fine-Tuning Platform

An end-to-end, enterprise-grade AI infrastructure for fine-tuning and deploying Large Language Models (LLMs). This platform abstracts the complexity of GPU orchestration, allowing you to go from raw data to a production-ready, autoscaling inference endpoint with a single click.

## 🚀 Key Features

- **Training Engine:** Support for LoRA, QLoRA, and Full Fine-tuning using Hugging Face TRL and Accelerate.
- **Model Registry:** Immutable versioning and lineage tracking for all model artifacts.
- **Deployment Engine:** vLLM-powered inference endpoints with OpenAI-compatible APIs.
- **Advanced Autoscaling:** KEDA-integrated "Scale to Zero" support to minimize GPU costs.
- **Agentic Control:** Integrated **MCP Server** for controlling the platform via AI agents (e.g., Claude).
- **Playground:** Side-by-side model comparison mode for qualitative evaluation.
- **Enterprise Ready:** Built-in observability (Prometheus), Audit Logging, RBAC, and usage-based Billing (Stripe).

## 🏗️ Architecture

The platform follows a microservices architecture orchestrated via Kubernetes:

- **Backend API (FastAPI):** The central control plane.
- **Frontend (Next.js):** Professional dashboard for management and evaluation.
- **Training Worker (Celery):** Distributed GPU workers for model training.
- **Deployment Manager:** Kubernetes operator for inference lifecycle.
- **MCP Server:** Interface for AI agents using the Model Context Protocol.

## 🛠️ Tech Stack

- **Backend:** Python, FastAPI, SQLAlchemy, PostgreSQL, Redis, Celery.
- **ML Infra:** PyTorch, Hugging Face (Transformers, PEFT, TRL), vLLM.
- **Frontend:** Next.js 14, TypeScript, Tailwind CSS, shadcn/ui, React Query.
- **DevOps:** Kubernetes, Docker, Terraform, Prometheus, Grafana, KEDA.

## 🚦 Getting Started

### Prerequisites

- Docker and Docker Compose
- Python 3.10+ (for local development)
- Node.js 20+ (for frontend development)

### Local Development (Quick Start)

1. **Clone the repository:**
   ```bash
   git clone <repo-url>
   cd ai-infrastructure
   ```

2. **Start Infrastructure Services:**
   ```bash
   docker-compose up -d
   ```

3. **Backend Setup:**
   ```bash
   cd apps/backend-api
   pip install -e .
   # Run migrations
   alembic upgrade head
   # Start server
   uvicorn src.main:app --reload
   ```

4. **Frontend Setup:**
   ```bash
   cd apps/frontend
   npm install
   npm run dev
   ```

## 📖 Documentation

- [API Reference](./apps/backend-api/README.md)
- [Deployment Guide](./docs/deployment.md)
- [MCP Server Integration](./apps/mcp-server/README.md)

## ⚖️ License

This project is licensed under the Apache 2.0 License.
