import os

base_path = r"c:\Users\jithin sai\OneDrive\Desktop\finalbot\backend"

directories = [
    "app/api/routes",
    "app/services/providers",
    "app/services/router",
    "app/services/memory",
    "app/services/search",
    "app/services/guardrails",
    "app/services/agents",
    "app/utils",
    "app/config",
    "app/schemas",
    "app/middleware",
    "app/core",
    "tests/api",
    "tests/core",
]

files = {
    "requirements.txt": """fastapi==0.111.0
uvicorn[standard]==0.29.0
pydantic==2.7.1
pydantic-settings==2.2.1
httpx==0.27.0
pytest==8.2.0
""",
    "Dockerfile": """FROM python:3.11-slim

WORKDIR /app
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000"]
""",
    ".dockerignore": """__pycache__
*.pyc
.env
.venv
venv/
tests/
""",
    ".env.example": """ENV=development
PORT=8000
LOG_LEVEL=INFO
VERSION=1.0.0
""",
    "README.md": """# Chatbot Backend

## Setup
1. Create virtual environment: `python -m venv venv`
2. Activate: `venv\\Scripts\\activate` (Windows)
3. Install dependencies: `pip install -r requirements.txt`
4. Copy `.env.example` to `.env`

## Run Locally
`uvicorn main:app --reload`

## Run Tests
`pytest`

## Run Docker
`docker build -t chatbot-backend .`
`docker run -p 8000:8000 --env-file .env.example chatbot-backend`
""",
    "main.py": """import time
from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse
from fastapi.exceptions import RequestValidationError
from starlette.exceptions import HTTPException as StarletteHTTPException

from app.api.routes import health
from app.config.settings import get_settings
from app.utils.logging import setup_logging
from app.utils.exceptions import validation_exception_handler, http_exception_handler, global_exception_handler
from app.middleware.logging import LoggingMiddleware

settings = get_settings()
setup_logging(settings.log_level)

app = FastAPI(
    title="AI Chatbot API",
    version=settings.version
)

# Exception Handlers
app.add_exception_handler(RequestValidationError, validation_exception_handler)
app.add_exception_handler(StarletteHTTPException, http_exception_handler)
app.add_exception_handler(Exception, global_exception_handler)

# Middleware
app.add_middleware(LoggingMiddleware)

# Routes
app.include_router(health.router)

@app.get("/")
async def root():
    return {"status": "ok", "version": settings.version, "environment": settings.env}

@app.on_event("startup")
async def startup_event():
    # Placeholder for startup logic
    pass

@app.on_event("shutdown")
async def shutdown_event():
    # Placeholder for shutdown logic
    pass
""",
    "app/config/settings.py": """from functools import lru_cache
from pydantic_settings import BaseSettings, SettingsConfigDict

class Settings(BaseSettings):
    env: str = "development"
    port: int = 8000
    log_level: str = "INFO"
    version: str = "1.0.0"

    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8", extra="ignore")

@lru_cache()
def get_settings():
    return Settings()
""",
    "app/schemas/health.py": """from pydantic import BaseModel

class HealthResponse(BaseModel):
    status: str
    version: str
    uptime: float
    environment: str
""",
    "app/api/routes/health.py": """import time
from fastapi import APIRouter, Depends
from app.schemas.health import HealthResponse
from app.config.settings import get_settings, Settings

router = APIRouter(tags=["health"])
START_TIME = time.time()

@router.get("/health", response_model=HealthResponse)
async def health_check(settings: Settings = Depends(get_settings)):
    return HealthResponse(
        status="healthy",
        version=settings.version,
        uptime=time.time() - START_TIME,
        environment=settings.env
    )

@router.get("/health/ready", response_model=HealthResponse)
async def health_ready(settings: Settings = Depends(get_settings)):
    return HealthResponse(
        status="ready",
        version=settings.version,
        uptime=time.time() - START_TIME,
        environment=settings.env
    )

@router.get("/version")
async def version(settings: Settings = Depends(get_settings)):
    return {"version": settings.version}
""",
    "app/utils/logging.py": """import logging
import json
from datetime import datetime

class JSONFormatter(logging.Formatter):
    def format(self, record):
        log_obj = {
            "timestamp": datetime.utcnow().isoformat() + "Z",
            "level": record.levelname,
            "name": record.name,
            "message": record.getMessage()
        }
        if hasattr(record, "request_id"):
            log_obj["request_id"] = record.request_id
        if hasattr(record, "path"):
            log_obj["path"] = record.path
        if hasattr(record, "method"):
            log_obj["method"] = record.method
        if hasattr(record, "latency"):
            log_obj["latency"] = record.latency
        if hasattr(record, "status"):
            log_obj["status"] = record.status
            
        return json.dumps(log_obj)

def setup_logging(log_level: str = "INFO"):
    logger = logging.getLogger()
    logger.setLevel(log_level)
    
    for handler in logger.handlers[:]:
        logger.removeHandler(handler)
        
    handler = logging.StreamHandler()
    handler.setFormatter(JSONFormatter())
    logger.addHandler(handler)
""",
    "app/middleware/logging.py": """import time
import uuid
import logging
from starlette.middleware.base import BaseHTTPMiddleware
from fastapi import Request

logger = logging.getLogger("api")

class LoggingMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next):
        request_id = str(uuid.uuid4())
        request.state.request_id = request_id
        
        start_time = time.time()
        
        try:
            response = await call_next(request)
            latency = (time.time() - start_time) * 1000
            
            logger.info(
                "Request processed",
                extra={
                    "request_id": request_id,
                    "path": request.url.path,
                    "method": request.method,
                    "latency": f"{latency:.2f}ms",
                    "status": response.status_code
                }
            )
            return response
        except Exception as e:
            latency = (time.time() - start_time) * 1000
            logger.error(
                "Request failed",
                extra={
                    "request_id": request_id,
                    "path": request.url.path,
                    "method": request.method,
                    "latency": f"{latency:.2f}ms",
                    "status": 500
                }
            )
            raise
""",
    "app/utils/exceptions.py": """from fastapi import Request
from fastapi.responses import JSONResponse
from fastapi.exceptions import RequestValidationError
from starlette.exceptions import HTTPException as StarletteHTTPException

async def validation_exception_handler(request: Request, exc: RequestValidationError):
    return JSONResponse(
        status_code=422,
        content={"error": "Validation Error", "details": exc.errors()}
    )

async def http_exception_handler(request: Request, exc: StarletteHTTPException):
    return JSONResponse(
        status_code=exc.status_code,
        content={"error": "HTTP Exception", "details": exc.detail}
    )

async def global_exception_handler(request: Request, exc: Exception):
    return JSONResponse(
        status_code=500,
        content={"error": "Internal Server Error", "details": str(exc)}
    )
""",
    "app/core/dependencies.py": """# Placeholder for Dependency Injection Container

class PlaceholderService:
    def __init__(self):
        pass

def get_placeholder_service():
    return PlaceholderService()
""",
    "tests/conftest.py": """import pytest
from fastapi.testclient import TestClient
from main import app

@pytest.fixture
def client():
    return TestClient(app)
""",
    "tests/api/test_health.py": """def test_root(client):
    response = client.get("/")
    assert response.status_code == 200
    assert response.json()["status"] == "ok"

def test_health(client):
    response = client.get("/health")
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "healthy"
    assert "version" in data

def test_health_ready(client):
    response = client.get("/health/ready")
    assert response.status_code == 200
    assert response.json()["status"] == "ready"

def test_version(client):
    response = client.get("/version")
    assert response.status_code == 200
    assert "version" in response.json()
""",
    "tests/core/test_config.py": """import os
from app.config.settings import Settings

def test_settings_default():
    settings = Settings(_env_file=None)
    assert settings.env == "development"
    assert settings.port == 8000

def test_settings_override():
    os.environ["ENV"] = "production"
    settings = Settings(_env_file=None)
    assert settings.env == "production"
    del os.environ["ENV"]
"""
}

for d in directories:
    dir_path = os.path.join(base_path, d)
    os.makedirs(dir_path, exist_ok=True)
    
for d in directories:
    parts = d.split('/')
    for i in range(1, len(parts) + 1):
        init_dir = os.path.join(base_path, *parts[:i])
        init_file = os.path.join(init_dir, "__init__.py")
        if not os.path.exists(init_file):
            open(init_file, 'a').close()

for file_path, content in files.items():
    full_path = os.path.join(base_path, file_path)
    os.makedirs(os.path.dirname(full_path) or base_path, exist_ok=True)
    with open(full_path, "w", encoding="utf-8") as f:
        f.write(content)

print("Backend skeleton generated successfully.")
