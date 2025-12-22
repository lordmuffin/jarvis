# Intelligent Burst Router

The **Intelligent Burst Router** is the traffic controller for Jarvis. It proactively manages requests between the local **Lemonade Server** and cloud providers (Gemini, Azure) to ensure optimal performance and reliability.

## Features

- **Proactive Health Checks**: Polls Lemonade `Health` and `Stats` every 30 seconds.
- **Capacity-Aware Routing**: Routes to cloud if local memory pressure is high (>90%).
- **Latency-Aware Routing**: Routes to cloud if local Time-To-First-Token (TTFT) exceeds threshold (default 2s).
- **Persistence**: Logs all query metrics to PostgreSQL.
- **Dashboard API**: Provides real-time system status to the Jarvis Console.

## Tech Stack

- **Framework**: Python 3.11 + FastAPI
- **Database**: SQLAlchemy + AsyncPG (PostgreSQL)
- **Deployment**: Docker + Kubernetes (Kustomize)

## Configuration

Environment Variables:

| Variable | Description | Default |
|----------|-------------|---------|
| `LEMONADE_SERVER_URL` | URL of local inference server | `http://localhost:8000` |
| `DATABASE_URL` | Async Postgres connection string | `postgresql+asyncpg://...` |
| `MAX_TTFT_MS` | TTFT threshold for switching to cloud | `2000` |

## Development

1. **Install Dependencies**:
   ```bash
   poetry install
   ```

2. **Run Locally**:
   ```bash
   poetry run uvicorn app.main:app --reload
   ```

3. **Run with Docker**:
   ```bash
   docker build -t jarvis-router .
   docker run -p 8000:8000 jarvis-router
   ```
