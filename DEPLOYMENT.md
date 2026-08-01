# Deployment Architecture

## Overview
The platform uses a containerized microservices architecture optimized for horizontal scaling, cloud-native deployment, and high availability.

## Component Architecture

### 1. Reverse Proxy & API Gateway (NGINX / HAProxy)
* **Role**: Acts as the single entry point to the system.
* **Responsibilities**: SSL/TLS termination, websocket upgrade handling (for streaming), load balancing across backend instances, and serving static frontend assets.

### 2. Frontend Application (React/Vite)
* **Role**: Client UI.
* **Responsibilities**: Packaged via multi-stage Docker builds. In production, static files are served either directly by NGINX or pushed to a global CDN (e.g., Cloudflare/AWS CloudFront) for reduced edge latency.

### 3. Backend Services (FastAPI)
* **Role**: Core application logic.
* **Responsibilities**: Runs via Uvicorn/Gunicorn. Designed to be entirely stateless. Session state and rate limits are pushed to Redis. This allows horizontal scaling (adding more Docker containers/Kubernetes pods) seamlessly under heavy load.

### 4. Relational Database (PostgreSQL)
* **Role**: Persistent source of truth.
* **Responsibilities**: Stores users, chat history, and configurations. Equipped with the `pgvector` extension to serve as the Vector DB for semantic memory. Deployed with a primary-replica architecture for read-heavy scaling.

### 5. Caching & Message Broker (Redis)
* **Role**: High-speed ephemeral storage.
* **Responsibilities**: Manages user rate limiting, caches session tokens, and acts as a message broker for background tasks (e.g., summarizing conversations asynchronously via Celery). Configured with persistence (RDB/AOF) to survive restarts.

## Observability & Logging Stack
* **Prometheus**: Scrapes the `/internal/metrics` endpoint of the Backend to aggregate system health, provider latency, and error rates.
* **Grafana**: Connects to Prometheus to provide real-time visual dashboards.
* **ELK Stack / Grafana Loki**: Aggregates structured JSON logs output from all Docker containers to allow distributed tracing and debugging.

## CI/CD Pipeline
* **Continuous Integration**: GitHub Actions executes on every Pull Request. It runs MyPy type checking, Ruff linting, Pytest test suites, and verifies Docker builds.
* **Continuous Deployment**: On merge to `main`, the pipeline builds production Docker images, tags them with the commit hash, pushes them to a Container Registry (e.g., Docker Hub, AWS ECR), and triggers a rolling update deployment to the production cluster (e.g., Kubernetes, Docker Swarm) ensuring zero downtime.
