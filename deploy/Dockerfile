# Build Stage
FROM golang:1.23-alpine AS builder

WORKDIR /app

# Install build dependencies
RUN apk add --no-cache git

COPY go.mod go.sum ./
RUN go mod download

COPY . .
RUN go build -o jarvis ./cmd/jarvis

# Runtime Stage
FROM ubuntu:22.04

# Install Runtime Dependencies
# - ca-certificates: For HTTPS
# - curl, unzip, git: Standard tools
# - lxc: For LXC management
# - docker interface (client) if running docker-in-docker
RUN apt-get update && apt-get install -y \
    ca-certificates \
    curl \
    unzip \
    git \
    lxc \
    lxc-templates \
    && rm -rf /var/lib/apt/lists/*

# Install Dagger CLI
RUN curl -L https://dl.dagger.io/dagger/install.sh | sh

# Install K9s
RUN curl -L -s https://github.com/derailed/k9s/releases/download/v0.32.4/k9s_Linux_amd64.tar.gz | tar xz -C /tmp && \
    mv /tmp/k9s /usr/local/bin/k9s && \
    chmod +x /usr/local/bin/k9s

# Install 1Password CLI
RUN curl -sS https://downloads.1password.com/linux/keys/1password.asc | gpg --import && \
    mkdir -p /etc/debsig/policies/AC2D62742012EA22 && \
    curl -sS https://downloads.1password.com/linux/debian/debsig/1password.pol | tee /etc/debsig/policies/AC2D62742012EA22/1password.pol && \
    mkdir -p /usr/share/debsig/keyrings/AC2D62742012EA22 && \
    curl -sS https://downloads.1password.com/linux/keys/1password.asc | gpg --dearmor > /usr/share/debsig/keyrings/AC2D62742012EA22/1password.gpg && \
    mkdir -p /usr/share/keyrings && \
    curl -sS https://downloads.1password.com/linux/keys/1password.asc | gpg --dearmor > /usr/share/keyrings/1password-archive-keyring.gpg && \
    echo "deb [arch=$(dpkg --print-architecture) signed-by=/usr/share/keyrings/1password-archive-keyring.gpg] https://downloads.1password.com/linux/debian/$(dpkg --print-architecture) stable main" | tee /etc/apt/sources.list.d/1password.list && \
    apt-get update && apt-get install -y 1password-cli

# Copy Binary
COPY --from=builder /app/jarvis /usr/local/bin/jarvis

# Setup directory for configuration
WORKDIR /workspace

ENTRYPOINT ["jarvis"]
