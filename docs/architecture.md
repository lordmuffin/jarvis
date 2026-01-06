# Jarvis CLI System Architecture

```mermaid
graph TD
    User([Platform Engineer]) -->|Commands| Jarvis[Jarvis CLI]
    
    subgraph "Jarvis Core"
        CLI[CLI Entry Point]
        Orchestrator[Orchestration Layer]
        Secrets[Secret Manager]
    end
    
    subgraph "Execution Plane"
        Dagger[Dagger Engine]
        LXC[LXC Host]
    end
    
    subgraph "Capabilities"
        K9s[K9s TUI]
        RemoteRunner[Remote Docker Execution]
    end
    
    Jarvis --> CLI
    CLI --> Orchestrator
    Orchestrator -->|Injects| Secrets
    Secrets -->|1Password| OP[1Password CLI]
    
    Orchestrator -->|Triggers| Dagger
    Orchestrator -->|Bootstraps| LXC
    Orchestrator -->|Launches| K9s
    
    Dagger -->|Executes Functions| Container[Containerized Tasks]
    LXC -->|Runs| SandboxedEnv[Sandboxed Environments]
    
    CLI -->|Connects| RemoteRunner
    RemoteRunner -->|Mirrors| LXC
```

## Description
- **Jarvis CLI**: The main entry point.
- **Dagger**: Used for pipeline execution and function orchestration.
- **LXC**: "The Real GOAT" runner for sandboxing and high performance.
- **1Password**: Integrated for secret injection (no secrets in disk).
- **K9s**: Embedded TUI for Kubernetes management.
