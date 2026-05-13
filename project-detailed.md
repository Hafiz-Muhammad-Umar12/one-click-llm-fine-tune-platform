# One-Click LLM Fine-Tuning Platform: Master Blueprint

This document serves as the master architectural blueprint and engineering specification for the One-Click LLM Fine-Tuning Platform. It outlines a production-grade, highly scalable AI infrastructure system designed for enterprise use cases.

---

## 1. PROJECT OVERVIEW

### What the Platform Does
The One-Click LLM Fine-Tuning Platform is an end-to-end AI infrastructure solution that abstracts the complexities of training, managing, and deploying Large Language Models (LLMs). It allows users to upload datasets, configure training runs (LoRA, QLoRA, full fine-tuning), monitor distributed training jobs in real-time, and deploy the resulting models to autoscaling inference endpoints with a single click.

### Business Goal
To democratize enterprise-grade AI adoption by providing a frictionless, managed infrastructure layer that rivals proprietary cloud AI services, reducing the time-to-market for custom LLM applications from months to hours.

### Technical Goal
To build a highly resilient, fault-tolerant, and horizontally scalable distributed system that orchestrates complex multi-GPU workloads across Kubernetes clusters, ensuring zero-downtime deployments and real-time observability.

### Target Users
- **AI/ML Engineers:** Seeking managed infrastructure without losing low-level control over training parameters.
- **Enterprise Software Developers:** Needing to integrate custom AI capabilities via API without deep ML expertise.
- **Data Scientists:** Focusing on dataset curation and model evaluation rather than infrastructure management.

### Enterprise Use Cases
- Customer support automation trained on proprietary knowledge bases.
- Code generation assistants tailored to internal enterprise codebases.
- Legal document summarization requiring strict data governance and sandboxing.
- Medical text analysis demanding high availability and auditability.

### Why This Platform Matters
Building ML infrastructure is notoriously difficult. Handling GPU driver issues, OOM errors, distributed training synchronization, and inference routing requires specialized knowledge. This platform commoditizes that expertise, offering it as a reliable, scalable service.

### Production Requirements
- **High Availability:** 99.9% uptime for API and gateway services.
- **Fault Tolerance:** Automatic retry of failed training jobs on different nodes; graceful degradation of services.
- **Security:** Strict tenant isolation, encrypted secrets, and comprehensive audit logs.
- **Observability:** Distributed tracing for every request, GPU-level metric collection.

### Scalability Requirements
- **Compute:** Ability to dynamically scale from 1 to 1000+ GPUs across multiple cloud providers or on-prem clusters.
- **Storage:** Handle terabytes of dataset and checkpoint data with high throughput and low latency.
- **Traffic:** Support thousands of concurrent inference requests per deployed model with autoscaling inference servers.

---

## 2. COMPLETE SYSTEM ARCHITECTURE

The platform utilizes a microservices architecture built on event-driven principles, orchestrated primarily via Kubernetes, ensuring loose coupling and independent scalability of components.

### 2.1 Component Architecture

1.  **Frontend (Next.js Application):** A scalable SPA acting as the user control plane. It interacts solely with the API Gateway.
2.  **API Gateway (Nginx/Envoy):** Handles SSL termination, rate limiting, and routes requests to the appropriate backend service.
3.  **Core API Backend (FastAPI):** The central control plane. Manages metadata (users, projects, datasets, job definitions) stored in PostgreSQL.
4.  **Auth Service:** Handles JWT issuance, validation, and RBAC (can be integrated into Core API or separate).
5.  **Job Orchestrator (Celery + Redis):** Manages the asynchronous execution of long-running tasks like dataset processing and model training.
6.  **Training Workers (Python/PyTorch):** GPU-enabled nodes that execute the actual training scripts. They pull jobs from the queue, download data from S3, run training, stream metrics to the observability stack, and upload checkpoints back to S3.
7.  **Deployment Orchestrator:** Interacts with the Kubernetes API to provision new inference services based on completed training runs.
8.  **Inference Servers (vLLM/SGLang):** High-throughput serving engines running on GPU nodes, exposed via an internal service mesh for routing.
9.  **Real-time Layer (WebSockets):** Pushes live logs and training metrics from workers to the frontend via a Pub/Sub mechanism (Redis).
10. **Storage (S3 Compatible):** Object storage for datasets, model weights, and checkpoints.
11. **Metadata Store (PostgreSQL):** Relational data for system state.
12. **Observability Stack (Prometheus/Grafana/Loki):** Collects metrics and logs from all services and workers.

### 2.2 Architecture Flows

#### **Request Flow (General API):**
Client -> API Gateway -> Auth Middleware -> Core API -> PostgreSQL/Redis -> Response.

#### **Training Execution Flow:**
1. User submits training config via Frontend.
2. Core API validates config, creates `training_job` record (State: Pending).
3. Core API enqueues job ID to Redis Queue (e.g., `gpu-queue`).
4. GPU Worker (listening to `gpu-queue`) claims job.
5. Worker updates job state to `Running` via API.
6. Worker downloads dataset from S3.
7. Worker initiates training script (HuggingFace Accelerate/TRL).
8. **Logging:** Worker continuously streams stdout/stderr to Redis Pub/Sub (for WebSockets) and Loki (for persistence).
9. **Metrics:** Worker pushes loss/throughput metrics to Prometheus/Redis.
10. Worker periodically saves checkpoints to S3.
11. Upon completion, Worker uploads final model to S3, updates job state to `Completed`, and triggers completion event.

#### **Deployment Flow:**
1. User clicks "Deploy" on a trained model.
2. Core API creates a `deployment` record.
3. Core API sends event to Deployment Orchestrator.
4. Orchestrator generates K8s manifests (Deployment, Service, HPA) for a vLLM container referencing the specific S3 model path.
5. Orchestrator applies manifests to K8s cluster.
6. K8s schedules GPU pods, pulls model weights (Init Container or dynamic loading), and starts vLLM.
7. Once health checks pass, Orchestrator updates deployment status to `Active`.
8. API Gateway routing is updated (via Ingress controller) to route traffic to the new service.

---

## 3. COMPLETE TECH STACK

### Frontend
*   **Next.js (App Router):** Chosen for server-side rendering (SSR), optimized routing, and enterprise-grade scalability. Better SEO for public-facing parts, and robust architecture for the dashboard.
*   **TypeScript:** Mandatory for type safety, reducing runtime errors, and improving developer experience in a large codebase.
*   **Tailwind CSS:** Utility-first CSS framework for rapid UI development and consistent design system implementation.
*   **shadcn/ui:** Unstyled, accessible components built on Radix UI and Tailwind. Provides complete control over the UI without the bloat of traditional component libraries.
*   **Zustand:** Minimal, fast state management for global UI state (e.g., active project context), avoiding Redux boilerplate.
*   **React Query (TanStack Query):** Handles data fetching, caching, synchronization, and optimistic updates. Essential for complex dashboards interacting with async APIs.
*   **Framer Motion:** For fluid, professional animations (e.g., progress bars, modal transitions) that give a premium feel.

### Backend
*   **FastAPI:** High-performance, async Python web framework. Native Pydantic support ensures strict API contract validation. Excellent for AI/ML backend integrations where Python is the lingua franca.
*   **Pydantic (v2):** Core data validation library. Ensures all incoming data and inter-service messages conform to exact schemas.
*   **SQLAlchemy (2.0) & Alembic:** Enterprise ORM and migration tool for robust database management. Async SQLAlchemy supports high-throughput non-blocking DB operations.
*   **Redis:** In-memory data store used for Celery broker, WebSocket pub/sub, rate limiting, and caching.
*   **Celery:** Distributed task queue for managing long-running, asynchronous AI workloads. Robust error handling and retry mechanisms.
*   **PostgreSQL:** The primary relational database. ACID compliant, highly reliable, and supports JSONB for flexible metadata storage.
*   **WebSockets:** For low-latency, real-time streaming of training logs and inference responses (chat UI).

### AI/ML Infrastructure
*   **Transformers (Hugging Face):** The industry standard library for state-of-the-art NLP models.
*   **PEFT & bitsandbytes:** Essential for Parameter-Efficient Fine-Tuning (LoRA, QLoRA), enabling training of massive models on consumer-grade or fewer enterprise GPUs by reducing memory footprint.
*   **TRL (Transformer Reinforcement Learning):** Provides tools for Supervised Fine-Tuning (SFT) and Direct Preference Optimization (DPO).
*   **Accelerate:** Simplifies running PyTorch code on distributed setups (multi-GPU, multi-node) without rewriting the training loop.
*   **vLLM:** Extremely high-throughput and memory-efficient LLM serving engine (using PagedAttention). Crucial for cost-effective inference.
*   **SGLang:** Alternative serving engine optimized for complex prompt workflows and structured generation.

### Infrastructure & DevOps
*   **Docker & Docker Compose:** Containerization for consistent environments across local dev, testing, and production.
*   **Kubernetes (K8s):** The orchestrator. Essential for managing dynamic GPU workloads, autoscaling deployments, and ensuring high availability.
*   **Nginx / K8s Ingress:** High-performance reverse proxy and API gateway.
*   **GitHub Actions:** CI/CD pipelines for automated testing, Docker image building, and infrastructure-as-code deployment.

### Observability
*   **Prometheus:** Time-series database for scraping and storing system and GPU metrics (utilization, memory).
*   **Grafana:** Dashboarding tool for visualizing Prometheus metrics and system health.
*   **OpenTelemetry:** Standardized distributed tracing to track requests as they move across frontend, backend, and inference services.
*   **Loki:** Log aggregation system designed to work seamlessly with K8s and Grafana.

### Storage & Other
*   **Qdrant:** High-performance vector database for RAG (Retrieval-Augmented Generation) features within the platform (e.g., querying documentation or dataset search).
*   **S3-compatible storage (AWS S3, MinIO):** Blob storage for massive datasets, model weights, and temporary artifacts.
*   **Better Auth:** Modern, secure, and extensible authentication library handling session management, OAuth, and generic Auth flows.

---

## 4. COMPLETE FOLDER STRUCTURE

This represents a monorepo setup, optimizing code sharing (e.g., Typescript schemas generated from OpenAPI) and streamlined CI/CD.

```text
one-click-ai-platform/
├── .github/                   # GitHub Actions CI/CD workflows
├── docs/                      # Architectural Decision Records (ADRs), API docs, internal wiki
├── k8s/                       # Kubernetes manifests (Helm charts or Kustomize)
│   ├── base/                  # Base manifests (Deployments, Services)
│   ├── overlays/              # Environment specifics (dev, staging, prod)
│   └── custom-resources/      # e.g., GPU Operator configs
├── infrastructure/            # Terraform/Pulumi scripts for cloud provisioning (EKS, RDS, S3)
├── packages/                  # Shared libraries across services
│   ├── config-eslint/         # Shared linting rules
│   ├── config-typescript/     # Shared TS configs
│   ├── shared-types/          # Generated TS types from OpenAPI specs
│   └── python-utils/          # Shared Python modules (e.g., logger, S3 client)
├── apps/
│   ├── frontend/              # Next.js Application
│   │   ├── src/
│   │   │   ├── app/           # App Router (pages, layouts)
│   │   │   ├── components/    # Reusable UI components (shadcn, composite)
│   │   │   ├── lib/           # Utility functions, axios clients, socket setup
│   │   │   ├── hooks/         # React Query hooks, custom hooks
│   │   │   ├── store/         # Zustand stores
│   │   │   └── types/         # Frontend-specific type definitions
│   │   ├── public/            # Static assets
│   │   └── package.json
│   │
│   ├── backend-api/           # Core FastAPI Service
│   │   ├── src/
│   │   │   ├── api/           # Routers (v1/datasets, v1/jobs)
│   │   │   ├── core/          # Config, security, dependencies, exception handlers
│   │   │   ├── db/            # SQLAlchemy models, Alembic migrations, session management
│   │   │   ├── schemas/       # Pydantic models (Request/Response)
│   │   │   ├── services/      # Business logic layer (DatasetService, JobService)
│   │   │   └── main.py        # FastAPI application entrypoint
│   │   ├── tests/             # Pytest suite
│   │   ├── Dockerfile
│   │   └── pyproject.toml
│   │
│   ├── websocket-server/      # Dedicated Node.js or Python service for high-connection pub/sub
│   │   └── src/               # Manages real-time log/metric streaming
│   │
│   ├── training-worker/       # Celery Worker + ML Logic
│   │   ├── src/
│   │   │   ├── tasks.py       # Celery task definitions (run_training)
│   │   │   ├── engine/        # PyTorch/TRL wrapper classes
│   │   │   │   ├── lora.py
│   │   │   │   ├── qlora.py
│   │   │   │   └── full.py
│   │   │   ├── utils/         # S3 sync, logging stream utilities
│   │   │   └── main.py        # Worker entrypoint
│   │   ├── Dockerfile.gpu     # Needs CUDA base image
│   │   └── requirements.txt
│   │
│   └── deployment-manager/    # Orchestrator for inference endpoints
│       └── src/               # Watches DB state, interacts with K8s API
├── docker-compose.yml         # Local development orchestration
├── Makefile                   # Common developer commands (make up, make test)
└── package.json               # Monorepo root
```

---

## 5. DATABASE ARCHITECTURE

PostgreSQL is used as the primary transactional store. We use a multi-tenant schema architecture (logical separation via an `organization_id` on critical tables) rather than schema-per-tenant to simplify migrations while maintaining security.

### Core Tables

#### `users`
- `id` (UUID, PK)
- `email` (VARCHAR, Unique, Indexed)
- `hashed_password` (VARCHAR)
- `is_active` (BOOLEAN)
- `created_at`, `updated_at` (TIMESTAMP)

#### `organizations`
- `id` (UUID, PK)
- `name` (VARCHAR)
- `billing_plan` (VARCHAR)
- `created_at` (TIMESTAMP)

#### `users_organizations` (M:N mapping)
- `user_id` (UUID, FK -> users.id)
- `organization_id` (UUID, FK -> organizations.id)
- `role` (VARCHAR) - e.g., 'owner', 'admin', 'member'

#### `api_keys`
- `id` (UUID, PK)
- `organization_id` (UUID, FK)
- `key_hash` (VARCHAR, Indexed) - Never store raw keys.
- `name` (VARCHAR)
- `last_used_at` (TIMESTAMP)

#### `datasets`
- `id` (UUID, PK)
- `organization_id` (UUID, FK, Indexed)
- `name` (VARCHAR)
- `description` (TEXT)
- `status` (VARCHAR) - Pending, Processing, Ready, Failed
- `format` (VARCHAR) - JSONL, CSV
- `s3_uri` (VARCHAR)
- `metadata` (JSONB) - Row count, token estimates, schema details
- `created_at` (TIMESTAMP)

#### `models` (Model Registry)
- `id` (UUID, PK)
- `organization_id` (UUID, FK)
- `base_model_name` (VARCHAR) - e.g., 'meta-llama/Llama-3-8b'
- `name` (VARCHAR)
- `description` (TEXT)

#### `training_jobs`
- `id` (UUID, PK)
- `organization_id` (UUID, FK, Indexed)
- `dataset_id` (UUID, FK)
- `model_id` (UUID, FK) - Link to registry
- `status` (VARCHAR, Indexed) - Queued, Running, Completed, Failed
- `hyperparameters` (JSONB) - Epochs, LR, LoRA r/alpha, batch size
- `infrastructure_config` (JSONB) - Requested GPUs (e.g., '1x A100')
- `output_s3_prefix` (VARCHAR)
- `started_at`, `completed_at` (TIMESTAMP)
- `error_message` (TEXT)

#### `deployments`
- `id` (UUID, PK)
- `organization_id` (UUID, FK)
- `model_id` (UUID, FK)
- `status` (VARCHAR) - Deploying, Active, Failed, Terminated
- `endpoint_url` (VARCHAR)
- `hardware_tier` (VARCHAR)
- `replica_count` (INTEGER)
- `created_at` (TIMESTAMP)

#### `usage_tracking` (Billing Ready)
- `id` (UUID, PK)
- `organization_id` (UUID, FK)
- `resource_type` (VARCHAR) - e.g., 'gpu_seconds', 'inference_tokens'
- `resource_id` (UUID) - Job ID or Deployment ID
- `quantity` (DECIMAL)
- `timestamp` (TIMESTAMP, Indexed for time-series aggregation)

### Scaling Considerations
- **Indexing:** Essential indexes on `organization_id` for tenant filtering, and `status` fields for queue workers.
- **JSONB:** Used heavily for configuration (`hyperparameters`, `metadata`) where strict schemas evolve rapidly in AI, preventing frequent DB migrations.
- **Connection Pooling:** PgBouncer must be deployed in front of Postgres to handle connection overhead from scalable K8s services.

---

## 6. AUTHENTICATION & SECURITY ARCHITECTURE

Security is paramount for an enterprise platform handling proprietary datasets.

### Authentication Flow
- **Better Auth** manages the primary flow. Users authenticate via email/password or SSO (Google, GitHub, SAML for enterprise).
- Upon success, an HttpOnly, secure, SameSite=Strict cookie is issued containing a short-lived JWT (Access Token) and a long-lived Refresh Token.
- **API Keys:** For programmatic access, users generate API keys in the dashboard. The raw key is shown ONCE. Only a bcrypt hash is stored in the `api_keys` table. API Gateway validates the `Authorization: Bearer <sk-...>` header against the hashed DB values using a high-performance caching layer (Redis) to avoid DB hits on every request.

### Authorization (RBAC & Tenant Isolation)
- Every request reaching the Core API is intercepted by a security dependency (FastAPI `Depends`).
- The dependency extracts the user/key, determines the `organization_id`, and validates the role.
- **Strict Row-Level Security (Logical):** Every database query must include `.where(organization_id == current_org.id)`. This prevents cross-tenant data leakage.

### Security Practices
- **Secrets Management:** K8s Secrets backed by HashiCorp Vault or AWS Secrets Manager. No secrets in environment variables in code repositories.
- **Sandboxing:** Training workers run in isolated Docker containers with strict resource limits (cgroups). Network policies block outbound internet access from training containers except to permitted S3 buckets and logging endpoints, preventing data exfiltration by malicious training scripts.
- **Secure Uploads:** Direct-to-S3 uploads using Presigned URLs. The backend never buffers massive dataset files in memory; it merely authorizes the upload and validates the S3 object afterward.

---

## 7. DATASET SYSTEM

The dataset pipeline ensures data quality before expensive GPU cycles are consumed.

### Pipeline Flow
1. **Upload Request:** Frontend requests a presigned S3 URL from the backend.
2. **Direct Upload:** Client uploads the file (JSONL, CSV) directly to the staging S3 bucket.
3. **Validation Task:** Backend creates a Celery task to validate the dataset.
4. **Processing Worker:**
    - Downloads the file.
    - **Validation:** Checks structural integrity (e.g., correct JSON parsing).
    - **Formatting:** Converts all formats (Alpaca, ChatML) into a standardized internal format (e.g., Hugging Face standard conversation format) based on the user-selected mapping.
    - **Analysis:** Calculates exact token counts using the target base model's tokenizer (crucial for accurate cost estimation and context length validation).
    - **Cleaning:** Removes exact duplicates or malformed rows.
    - **Splitting:** Automatically generates a consistent train/validation split (e.g., 95/5) and saves them as separate parquet files in S3 for fast loading by Hugging Face `datasets` library.
5. **Completion:** Updates `datasets` table with metadata (token counts, valid rows) and sets status to `Ready`.

### Storage Strategy
Raw uploads are kept in a cold-tier storage. Processed `.parquet` files (optimized for column-oriented reading and chunking during training) are kept in hot storage for rapid loading by the training workers.

---

## 8. TRAINING ENGINE

The training engine is built on robust asynchronous workers designed to handle failures gracefully.

### Architecture
- **Job Submission:** The Core API validates hyperparameters against the model's constraints, creates the `training_job`, and pushes the ID to a Redis list (`queue:training:a100`).
- **GPU Scheduling:** K8s manages a pool of Node Groups (e.g., A10G nodes, A100 nodes). The Deployment Orchestrator can dynamically scale training pods based on queue length (KEDA integration).
- **Execution Script:** The worker container runs a heavily instrumented Python script. It utilizes `accelerate` for multi-GPU distribution and `trl` for SFT/DPO workflows.

### Advanced Features Supported
- **PEFT/LoRA:** Default for cost-effective training. Supports configurable rank (`r`), `alpha`, and target modules.
- **QLoRA:** Utilizes `bitsandbytes` 4-bit quantization on the base model, allowing large models (e.g., Llama-70B) to be fine-tuned on single or dual GPUs.
- **Memory Management:** Implements gradient checkpointing, fused optimizers (AdamW_8bit), and dynamic batch sizing to strictly prevent CUDA OOM errors.
- **Resilience:** Periodically syncs checkpoint directories directly to S3. If a node fails, K8s restarts the pod, the worker detects an existing checkpoint in S3, downloads it, and resumes training automatically.

### Live Telemetry
- The training script overrides standard PyTorch logging.
- A background thread pushes JSON-formatted metrics (step, loss, learning_rate, eval_loss) and raw console text output directly to Redis Pub/Sub channels keyed by `job_id`.

---

## 9. MODEL REGISTRY SYSTEM

The Model Registry acts as the central source of truth for all artifacts produced by the platform.

### Structure
- Models are logically grouped under base models.
- A `Model` entity points to specific artifacts in S3 (adapter weights for LoRA, or full weights).
- **Metadata:** Captures full lineage. A model record includes the exact ID of the dataset used, the training job ID that produced it, and the exact hyperparameter snapshot.
- **Comparison:** Enables the frontend to present side-by-side evaluations of different models trained on the same dataset but with different hyperparameters (e.g., comparing Loss curves).

---

## 10. MODEL DEPLOYMENT SYSTEM

Deploying a model transitions it from cold storage to an active, HTTP-accessible inference endpoint.

### Pipeline
1. User configures deployment (selects hardware tier, e.g., '1x L4').
2. Core API marks status `Deploying`.
3. Orchestrator generates a Kubernetes deployment manifest.
    - **Engine:** Uses `vLLM` container image.
    - **Model Loading:** If it's a LoRA adapter, vLLM supports dynamic LoRA loading. The pod pulls the base model (often from a shared network volume to save time) and loads the specific adapter weights from S3 on startup.
4. **Service & Ingress:** Creates a K8s Service and Ingress rule routing `https://api.platform.com/v1/inference/{deployment_id}` to the specific pod.
5. **Autoscaling:** K8s HPA (Horizontal Pod Autoscaler) is configured to scale pods based on custom metrics (e.g., vLLM queue length) exported to Prometheus.
6. **Health Checks:** Kubernetes readiness probes query vLLM's `/health` endpoint. Status turns `Active` only when the model is fully loaded into VRAM and ready to serve.

---

## 11. PLAYGROUND SYSTEM

The playground is a critical UI component for qualitative evaluation.

- **Interface:** A dual-pane chat interface resembling standard LLM applications.
- **Streaming:** Utilizes Server-Sent Events (SSE) from the vLLM endpoint directly through the API gateway to the Next.js frontend, ensuring a snappy, typing-effect experience.
- **Controls:** Sliders for Temperature, Top-P, Presence Penalty, and Max Tokens.
- **Comparison Mode:** Allows routing the same prompt to two different deployment endpoints simultaneously, rendering responses side-by-side for human evaluation.

---

## 12. MCP INTEGRATION SYSTEM (Model Context Protocol)

The platform exposes an MCP server allowing agents (like Claude or custom tools) to programmatically interact with the infrastructure.

### Architecture
- A standalone fastAPI service acting as the MCP Server, implementing the standard MCP JSON-RPC protocol over stdio (for local agents) or SSE/WebSockets.
- Authenticated via standard API keys.

### MCP Tools
- `list_datasets`: Returns available datasets and metadata.
- `trigger_training`: Initiates a training job. Schema includes `dataset_id`, `base_model`, `hyperparameters`.
- `get_training_status`: Returns live metrics and status of a job.
- `deploy_model`: Provisions an endpoint for a trained model.
- `test_inference`: Sends a prompt to a deployed model and returns the response.

*Workflow:* An agent can be instructed: "Fine-tune Llama-3 on my customer support data and tell me when it's deployed." The agent uses MCP tools to upload, train, monitor, and deploy autonomously.

---

## 13. OBSERVABILITY & MONITORING

Comprehensive observability is non-negotiable for AI infrastructure.

### Metrics (Prometheus)
- **Infrastructure:** CPU, Memory, Network I/O.
- **GPU (DCGM Exporter):** GPU Utilization %, VRAM Usage %, Power Draw, Temperature. Crucial for detecting stranded resources or inefficient code.
- **App/Business:** Number of active training jobs, job failure rate, average inference latency (TTFT - Time To First Token, TPOT - Time Per Output Token).

### Tracing (OpenTelemetry)
- Every request generates a Trace ID at the Next.js frontend or Nginx gateway.
- This ID propagates through the FastAPI backend, into the Celery task context, and down to the vLLM inference server. Allows pinpointing bottlenecks (e.g., "Is the database slow, or is the model taking too long to generate?").

### Logs (Loki)
- Centralized logging from all pods. Filterable by `organization_id` or `job_id` via Grafana, accessible internally to engineers and externally (scoped) to users via the dashboard.

---

## 14. FRONTEND ARCHITECTURE

### Structure (Next.js App Router)
- `app/(auth)/`: Login, registration, password reset pages.
- `app/(dashboard)/`: Main application wrapped in an Auth Guard and Layout with a sidebar.
  - `projects/[id]/datasets/`
  - `projects/[id]/training/`
  - `projects/[id]/deployments/`
- `app/api/`: Next.js Route Handlers (mostly used for proxying secure requests or handling webhooks, not primary business logic).

### State Management
- **Zustand:** Holds UI state (e.g., `isSidebarOpen`, `currentOrganizationId`).
- **React Query:** Manages server state. All backend API calls use query hooks (`useQuery`, `useMutation`) with appropriate invalidation strategies to keep the UI in sync without manual refetching.

### Reusable Components (shadcn/ui)
- A strict design system using Tailwind classes grouped into reusable components (DataTables for jobs, Forms with Zod validation for complex hyperparameters).
- **Error Boundaries:** Wrap major sections to prevent whole-app crashes if a component fails to render data.

---

## 15. BACKEND ARCHITECTURE

### Layered Architecture (FastAPI)
- **Routers (`api/`):** Define endpoints, depend on authentication, extract request data, and pass it to Services.
- **Services (`services/`):** Contain core business logic. E.g., `JobService.create_job()` validates inputs, handles DB transactions, and enqueues Celery tasks. They do not know about HTTP requests.
- **Repositories (`db/repositories/`):** Abstraction over SQLAlchemy. Handle raw DB operations. E.g., `JobRepository.get_by_id()`.
- **Schemas (`schemas/`):** Pydantic models for validation. Distinct schemas for DB Creation (`JobCreate`), DB Updates (`JobUpdate`), and API Responses (`JobResponse`).

### Async Design
The entire FastAPI layer uses `async def` and `async_session` from SQLAlchemy to handle thousands of concurrent requests without blocking the event loop.

---

## 16. API DESIGN

RESTful JSON API with consistent conventions.

### Base URL: `https://api.platform.com/v1/`

### Example Endpoints:

#### `POST /jobs` (Create Training Job)
- **Auth:** Bearer Token required.
- **Request Body (JSON):**
  ```json
  {
    "dataset_id": "uuid",
    "base_model": "meta-llama/Meta-Llama-3-8B-Instruct",
    "method": "qlora",
    "hyperparameters": { "epochs": 3, "learning_rate": 2e-4, "lora_r": 16 }
  }
  ```
- **Validation:** Pydantic ensures `learning_rate` is a float within bounds, `base_model` is supported.
- **Response (202 Accepted):** `{"job_id": "uuid", "status": "queued"}`

#### `GET /jobs/{job_id}/logs/stream`
- **Protocol:** WebSocket.
- **Auth:** Token passed via subprotocol or initial message.
- **Response:** Continuous stream of JSON objects containing timestamp and log line.

#### `POST /deployments/{id}/v1/chat/completions`
- OpenAI-compatible inference endpoint for seamless integration with existing tools (Langchain, LlamaIndex).

---

## 17. COMPLETE USER FLOWS

### Flow: Training Creation & Monitoring
1.  **UI:** User selects dataset, model, configures params, clicks "Start Training".
2.  **Frontend:** POST `/v1/jobs` via React Query mutation.
3.  **Backend (API):** Validates, saves to DB, pushes to Redis. Returns `job_id`.
4.  **Frontend:** Redirects to Job Detail page (`/jobs/{job_id}`).
5.  **Frontend:** Initiates WebSocket connection to `/jobs/{job_id}/logs/stream` and sets up polling (or SSE) for `GET /jobs/{job_id}/metrics`.
6.  **Backend (Worker):** Picks up job, starts training, publishes logs to Redis Pub/Sub.
7.  **Backend (WebSocket Server):** Subscribes to Redis channel, pushes logs to Frontend.
8.  **UI:** Terminal component live-updates with logs. Line charts dynamically render loss metrics.

---

## 18. STEP-BY-STEP IMPLEMENTATION ROADMAP

### Phase 1: Foundation (The Core Framework)
- Monorepo setup, Database design, Core API skeleton, Auth system.

### Phase 2: Data Pipeline (The Fuel)
- Dataset upload logic, S3 integration, Processing workers, Dataset UI.

### Phase 3: Training Engine (The Core Value)
- GPU worker infrastructure, Celery queues, PyTorch/TRL integration, Log streaming, Metrics collection.

### Phase 4: Serving & Inference (The Output)
- Kubernetes deployment orchestrator, vLLM integration, Playground UI, OpenAI-compatible endpoints.

### Phase 5: Productionization (The Enterprise Standard)
- Comprehensive testing, Observability stack (Prometheus/Grafana), Rate limiting, CI/CD pipelines, Documentation.

---

## 19. PHASE 1 IMPLEMENTATION (Detailed Steps)

**Goal:** Establish the underlying infrastructure and "Hello World" API and UI.

1.  **Repository Initialization:** Create standard directories, setup `package.json` for monorepo tools (Turborepo or Yarn Workspaces).
2.  **Docker Setup:** Create `docker-compose.yml` defining PostgreSQL, Redis, backend, frontend, and a mock worker container.
3.  **Backend Initialization:**
    - Initialize FastAPI app.
    - Setup SQLAlchemy with async engine.
    - Implement Alembic migrations. Generate initial migration for `users`, `organizations`, `api_keys`.
    - Setup Dependency Injection for database sessions.
4.  **Auth Setup:** Integrate authentication library, secure routes with dependencies.
5.  **Frontend Initialization:**
    - `npx create-next-app@latest frontend --typescript --tailwind --eslint`
    - Setup shadcn/ui.
    - Create basic layout, sidebar, and Auth pages.
6.  **CI/CD:** Create GitHub Actions to run ESLint, Pytest on PRs.

---

## 20. PHASE 2 IMPLEMENTATION (Datasets)

1.  **Database Updates:** Alembic migration for `datasets` table.
2.  **S3 Integration:** Implement `StorageService` in Python using `boto3` to generate presigned URLs.
3.  **Backend API:** Create `POST /datasets` (get URL) and `PUT /datasets/{id}/status` (webhook for upload completion).
4.  **Celery Setup:** Configure Celery application connected to Redis broker.
5.  **Processing Task:** Write Python script using `pandas` and HuggingFace `datasets` to read JSONL, validate format, tokenize, and save as `.parquet`.
6.  **Frontend UI:** Build drag-and-drop file upload component with progress bars. Data table to list datasets and their processing status.

---

## 21. PHASE 3 IMPLEMENTATION (Training Pipeline)

1.  **Database Updates:** Migrations for `models` and `training_jobs`.
2.  **API:** `POST /jobs` endpoint to configure and enqueue runs.
3.  **GPU Worker Dockerfile:** Create robust Dockerfile using NVIDIA CUDA base image, installing PyTorch, Transformers, TRL, accelerate, bitsandbytes.
4.  **Training Script:** Write the core `train.py`. It must accept command-line arguments (passed by Celery), handle downloading data, configuring LoRA, running the Trainer loop, and handling exceptions to update DB status on failure.
5.  **Log Streaming:** Implement custom callback in Hugging Face Trainer to push `logger.info` and metrics dicts to Redis Pub/Sub.
6.  **WebSocket Service:** Build the FastAPI WebSocket endpoint to connect clients to Redis streams.
7.  **Frontend UI:** Build complex configuration form (hyperparameters). Build the "Active Run" dashboard with a terminal-like log view and Recharts for loss curves.

---

## 22. PHASE 4 IMPLEMENTATION (Deployments)

1.  **Database Updates:** Migrations for `deployments`.
2.  **Kubernetes Orchestrator Layer:**
    - Create Python service using `kubernetes` client library.
    - Define templates for Deployment, Service, Ingress.
3.  **Inference Server:** Prepare standard vLLM Docker image configuration. Ensure it can pull weights from S3 on startup using InitContainers or custom entrypoints.
4.  **Backend API:** `POST /deployments`, `GET /deployments/{id}`.
5.  **Frontend UI:** Deployment management dashboard.
6.  **Playground:** Build the chat interface UI interacting with the deployed vLLM endpoints via streaming SSE.

---

## 23. PHASE 5 IMPLEMENTATION (Monitoring & Security)

1.  **Prometheus Integration:** Expose `/metrics` endpoint on FastAPI. Deploy Node Exporter and DCGM Exporter to K8s nodes.
2.  **Grafana:** Create dashboards for overall system health and individual job GPU utilization.
3.  **Rate Limiting:** Implement Redis-based rate limiting on public API routes to prevent abuse.
4.  **Audit Logs:** Implement middleware to log every state-mutating request (POST/PUT/DELETE) to a separate `audit_logs` table for compliance.

---

## 24. TESTING STRATEGY

- **Unit Tests (Backend/Pytest):** Test services, validation logic, and utility functions in isolation using mocked database sessions and mocked S3 clients.
- **Unit Tests (Frontend/Vitest):** Test complex hooks and Zod validation schemas.
- **Integration Tests (Backend):** Use `TestClient` and a dedicated test PostgreSQL database to test full API flows (Create dataset -> Create Job) ensuring DB state is correct.
- **E2E Tests (Playwright):** Automate the entire user journey: Login, upload file, configure training, verify job status changes.
- **GPU Tests:** Specialized test suite requiring a GPU node to ensure the actual training script (`train.py`) executes without syntax errors or immediate OOMs on dummy data.

---

## 25. DEVOPS & CI/CD

- **GitHub Actions:**
    - **PR Gate:** Runs linting, unit/integration tests, builds Docker images to ensure they compile.
    - **Main Merge:** Builds production Docker images, tags with Git SHA, pushes to Container Registry (ECR/GCR).
- **Deployment Automation:** ArgoCD or Flux for GitOps. Changes to the `k8s/` directory automatically trigger cluster reconciliation.
- **Environments:** Strict separation between Staging (sandbox DB, small K8s cluster) and Production.
- **Rollback:** Versioned Docker images allow instant rollback by changing image tags in Kubernetes manifests.

---

## 26. KUBERNETES ARCHITECTURE

- **Namespaces:** Logical separation between `platform-services` (API, Auth) and `tenant-workloads` (Training jobs, deployments).
- **GPU Scheduling:** Use NodeSelectors/Taints to ensure standard API pods don't schedule on expensive GPU nodes, reserving them strictly for workers and vLLM.
- **Autoscaling (Karpenter/Cluster Autoscaler):** Dynamically provision new GPU nodes from the cloud provider when the queue backs up, and scale them down to zero when idle to manage costs aggressively.

---

## 27. SCALABILITY PLAN

- **API/Frontend:** Stateless containers. Scale horizontally infinitely by increasing replica count behind the load balancer.
- **Database:** Vertical scaling initially (bigger RDS instance). Use read replicas for heavy read operations (dashboard lists). Partition tables (`training_logs`) by time if necessary.
- **Queue/Workers:** Decoupled architecture allows scaling workers completely independently of the web tier. If the queue is full, spin up more worker pods.
- **Inference:** vLLM natively supports continuous batching. K8s HPA scales replica count of inference endpoints based on concurrent request load.

---

## 28. PRODUCTION READINESS CHECKLIST

- [ ] Security: Penetration testing, Secrets rotated, RBAC strictly enforced via unit tests.
- [ ] Performance: DB Indexes applied to all foreign keys and query patterns. Load testing API gateway.
- [ ] Observability: Alerts configured in Grafana for API 500s, Job failure rate spikes, Node OOMs.
- [ ] Backups: Automated daily RDS snapshots, Point-in-Time Recovery enabled.
- [ ] Fallbacks: Handling S3 API rate limits or transient network errors using robust retry libraries (Tenacity).

---

## 29. ENGINEERING BEST PRACTICES

- **Clean Architecture:** Strict separation of concerns (Routers -> Services -> Repositories). The web layer must not contain business logic.
- **Strong Typing:** Pydantic and TypeScript everywhere. No `any` types. Contracts between frontend and backend strictly enforced.
- **Error Handling:** Standardized error responses (Problem Details format). Never leak stack traces to the client.
- **Idempotency:** Crucial for distributed systems. Ensure retrying a task (e.g., job creation) doesn't create duplicate resources.

---

## 30. FINAL DEVELOPMENT STRATEGY

1.  **Prioritize the Critical Path:** The highest risk is the GPU orchestrator and training script reliability. Build a robust CLI-based prototype of the worker *first* to prove out the ML pipeline before wrapping it in the complex web UI.
2.  **Mock Early, Integrate Later:** Build the frontend against a mocked API or openAPI spec while the backend team builds the real endpoints.
3.  **Fail Fast:** Implement stringent dataset validation upfront. Bad data shouldn't reach the GPU queue.
4.  **Enterprise Mindset:** Assume every system component will fail. Design for graceful recovery (e.g., resumable training checkpoints).

This document serves as the foundation. Implementation will follow these architectural guidelines strictly.