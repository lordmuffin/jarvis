# Jarvis
**The Intelligent Platform Engineering Ecosystem**

Jarvis is a "Platform-in-a-Box" designed to be the single entry point for managing infrastructure, deployments, and automation. It serves as an intelligent CLI that orchestrates tools like Dagger, LXC, and Kubernetes (K9s) to provide a seamless platform engineering experience.

## 🧠 Core Philosophy: The Agentic Controller

Jarvis operates as an **Agentic Controller**. It doesn't just run scripts; it observes, plans, and executes.

- **Control Plane**: The Jarvis CLI (Go) acts as the brain.
- **Execution Plane**: [Dagger](https://dagger.io) acts as the muscle, running portable, containerized functions.
- **Isolation Plane**: [LXC](https://linuxcontainers.org/) provides "Real GOAT" sandboxing for heavy-duty tasks.
- **Observability**: Integrated [K9s](https://k9scli.io/) bridge for deep Kubernetes introspection.
- **Security**: Native **1Password** integration—secrets are injected in memory, never written to disk.

See the [Architecture Diagram](docs/architecture.md) for more details.

---

## 🚀 Features

### 1. Dagger Function Engine
Run platform tasks as portable Dagger pipelines.
```bash
# Run a specific Dagger function
jarvis run deployments:update-image
```

### 2. LXC Integration ("The Real GOAT")
Bootstrap and manage Linux Containers for robust, isolated testing environments.
```bash
# Create a new Ubuntu container
jarvis lxc bootstrap my-test-env

# Snapshot a container
jarvis lxc snapshot my-test-env
```

### 3. Kubernetes Management
Launch a fully configured K9s TUI directly from Jarvis.
```bash
# Open K9s
jarvis k9s
```


### 4. OpenTofu Integration
Manage infrastructure with OpenTofu (formerly Terraform) using Dagger pipelines.
```bash
# Plan infrastructure
jarvis tofu plan

# Apply infrastructure
jarvis tofu apply
```

### 5. Portable Execution
Jarvis runs identically on your MacBook and inside a remote Docker container.
- **Local Mode**: Uses your local Docker/LXC agents.
- **Remote Mode**: Connects to remote Dagger engines via `REMOTE_DAGGER_ADDR`.

---

## 🛠 Installation & Usage

### 1. Build from Source
Requirements: Go 1.23+
```bash
go build -o jarvis ./cmd/jarvis
```

### 2. Run with Docker
The "Platform-in-a-Box" experience. This image includes all dependencies (Dagger, K9s, LXC, 1Password).
```bash
docker build -t jarvis-cli -f deploy/Dockerfile .
docker run -it -v /var/run/docker.sock:/var/run/docker.sock jarvis-cli
```

### 3. Configuration
Configure Jarvis via Environment Variables:

| Variable | Description | Default |
|----------|-------------|---------|
| `REMOTE_DAGGER_ADDR` | Address of a remote Dagger engine (TCP) | "" (Local) |
| `JARVIS_ENABLE_LXC` | Enable LXC management features | `false` |
| `JARVIS_USE_OP` | Enable 1Password Secret Injection | `false` |

---

## 📂 Project Structure

```
├── cmd/jarvis          # Main CLI Entry Point
├── deploy              # Docker packaging
├── docs                # Architecture & Plans
├── internal
│   ├── dagger          # Dagger Engine Executor
│   ├── k9s             # K9s TUI Bridge
│   ├── lxc             # LXC Management Layer
│   └── secrets         # 1Password Integration
└── services            # (Monorepo) Backend microservices
```

## 📜 License
MIT
