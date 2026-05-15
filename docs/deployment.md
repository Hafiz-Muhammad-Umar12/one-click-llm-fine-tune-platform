# Deployment Guide

This guide covers the deployment of the One-Click AI Fine-Tuning Platform in both Development and Production environments.

## 1. Development (Docker Compose)

The easiest way to run the entire stack locally is using Docker Compose.

```bash
docker-compose up --build
```

- **Frontend:** http://localhost:3000
- **Backend API:** http://localhost:8000/docs
- **Postgres:** localhost:5432
- **Redis:** localhost:6379

## 2. Production (Kubernetes)

The platform is designed to be deployed on Kubernetes, ideally on AWS EKS or GCP GKE.

### Infrastructure Provisioning
Use Terraform to provision the cluster and GPU node groups:

```bash
cd infrastructure/terraform
terraform init
terraform apply
```

### Deploying Services
Apply the base manifests or use the Helm charts:

```bash
kubectl apply -k k8s/overlays/prod
```

### Autoscaling with KEDA
Ensure KEDA is installed in the cluster to support "Scale to Zero" for inference endpoints:

```bash
helm repo add kedacore https://kedacore.github.io/charts
helm install keda kedacore/keda --namespace keda --create-namespace
```

## 3. Configuration

Key environment variables to configure for production:

| Variable | Description |
|----------|-------------|
| `DATABASE_URL` | Async SQLAlchemy connection string for RDS. |
| `S3_BUCKET` | Bucket for storing model weights and datasets. |
| `STRIPE_API_KEY` | For processing payments. |
| `K8S_NAMESPACE` | Namespace where training jobs will be scheduled. |

## 4. GPU Optimization

For high-performance inference, ensure the nodes have the NVIDIA Device Plugin installed and `vLLM` is configured with the correct `--tensor-parallel-size` matching the number of GPUs on the node.
