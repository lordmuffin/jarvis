# Jarvis
**The MONOREPO Executive Assistant**

This repository contains the microservices and applications that power Jarvis, a personal knowledge automation platform.

## Architecture

The system is composed of several key components:

### Apps
- **[Jarvis Console](apps/jarvis-console/README.md)**: The administrative "Control Plane" dashboard. Built with Next.js, it provides system monitoring (HUD), traffic control visualization, and configuration management.

### Services
- **[Intelligent Burst Router](services/router/README.md)**: A FastAPI-based "Smart Router" that manages traffic between the local Lemonade Server and Cloud Providers (Gemini/Azure). It makes routing decisions based on Time-To-First-Token (TTFT) and System Capacity (Memory Pressure).
- **Provocateur Interviewer**: Real-time voice interview service.
- **Jarvis Core**: Core logic and integrations.

### Infrastructure
- **Lemonade Server**: Local LLM Inference Server.
- **Qdrant**: Vector Database for RAG.
- **NATS**: Messaging System.
- **CloudNativePG**: PostgreSQL for persistence.

## Getting Started

### Prerequisites
- Docker & Docker Compose
- Python 3.11+
- Node.js 18+

### Local Development
To start the entire stack locally:

```bash
docker-compose up --build
```

This will spin up:
- **Router**: `http://localhost:8000`
- **Console**: `http://localhost:3000`
- **PostgreSQL**: `localhost:5432`

## Deployment

The project uses Kubernetes (Kustomize) for deployment.
- **Router**: `services/router/kustomization.yaml`
- **Qdrant**: `infrastructure/components/qdrant`
- **NATS**: `infrastructure/components/nats`
