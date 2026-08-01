# Project Structure

## Backend (`/backend`)
* **`/backend/api/`** - FastAPI routes, controllers, and middleware for all exposed endpoints.
* **`/backend/core/`** - Core business logic, application configuration schemas, and the main orchestrator.
* **`/backend/providers/`** - AI provider implementations (OpenAI, Anthropic, Gemini, etc.) mapping to abstract interfaces.
* **`/backend/services/`** - Independent domain services (Memory, Search, Authentication, Metrics).
* **`/backend/models/`** - Pydantic schemas (requests/responses) and SQLAlchemy database models.
* **`/backend/db/`** - Database connection setup, session management, and Alembic migrations.
* **`/backend/utils/`** - Helper functions, standard logging formatters, and global error handlers.
* **`/backend/tests/`** - Unit and integration tests ensuring backend reliability and coverage.
* **`/backend/Dockerfile`** - Containerization instructions for the FastAPI Python application.

## Frontend (`/frontend`)
* **`/frontend/src/components/`** - Reusable React presentation components (Buttons, Inputs, Modals).
* **`/frontend/src/features/`** - Feature-based logical modules (Chat Window, Settings Panel, Auth Flows).
* **`/frontend/src/hooks/`** - Custom React hooks encapsulating state management and side effects.
* **`/frontend/src/services/`** - API client definitions for communicating with backend REST/SSE endpoints.
* **`/frontend/src/store/`** - Global state management store (e.g., Zustand) for conversation and user context.
* **`/frontend/src/styles/`** - Global CSS, Tailwind configurations, and Framer Motion animation variants.
* **`/frontend/src/utils/`** - Frontend utilities, date formatters, and validation helpers.
* **`/frontend/Dockerfile`** - Containerization instructions for building and serving the React application.

## Infrastructure (`/infrastructure`)
* **`/infrastructure/docker-compose.yml`** - Local development and testing environment orchestration.
* **`/infrastructure/nginx/`** - Reverse proxy configurations, SSL termination, and load balancing rules.
* **`/infrastructure/monitoring/`** - Prometheus scraping configurations and Grafana dashboard templates.

## Scripts (`/scripts`)
* **`/scripts/setup.sh`** - Environment initialization and dependency installation script for new developers.
* **`/scripts/migrate.sh`** - Database migration execution script invoked during CI/CD.
* **`/scripts/backup.sh`** - Automated script for dumping Database and Redis state for disaster recovery.

## Configuration (`/config`)
* **`/config/provider_routing.yaml`** - Declarative configuration for default models, failover chains, and provider priorities.
* **`/config/rate_limits.yaml`** - Definition of token and request rate limits segregated by user subscription tier.
