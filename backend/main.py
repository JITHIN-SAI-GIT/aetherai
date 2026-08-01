import time
import logging
from contextlib import asynccontextmanager
from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse
from fastapi.middleware.cors import CORSMiddleware
from fastapi.exceptions import RequestValidationError
from starlette.exceptions import HTTPException as StarletteHTTPException

from app.api.routes import health, internal
from app.api.v1 import chat, models
from app.api.v1.errors import open_ai_exception_handler, HTTPException
from app.config.settings import get_settings
from app.utils.logging import setup_logging
from app.utils.exceptions import validation_exception_handler, http_exception_handler, global_exception_handler
from app.middleware.logging import LoggingMiddleware
from app.core.dependencies import get_connection_pool, get_performance_metrics

settings = get_settings()
setup_logging(settings.log_level)

logger = logging.getLogger("main")


from app.db.mongo import MongoDBManager

@asynccontextmanager
async def lifespan(app: FastAPI):
    """
    Manages the lifecycle of shared resources.
    startup: initialises the shared HTTP connection pool + performance metrics.
    shutdown: cleanly drains and closes all connections.
    """
    # ── Startup ───────────────────────────────────────────────────────────────
    pool = get_connection_pool()
    await pool.startup()
    await MongoDBManager.connect()
    
    from app.db.indexes import setup_indexes
    await setup_indexes()

    # Initialise performance metrics (also wires track_stage → metrics)
    get_performance_metrics()

    logger.info("Application startup complete")
    yield

    # ── Shutdown ──────────────────────────────────────────────────────────────
    await MongoDBManager.disconnect()
    await pool.shutdown()
    logger.info("Application shutdown complete")


app = FastAPI(
    title="AI Chatbot API",
    version=settings.version,
    lifespan=lifespan,
)

# Exception Handlers
app.add_exception_handler(RequestValidationError, validation_exception_handler)
app.add_exception_handler(HTTPException, open_ai_exception_handler)
app.add_exception_handler(StarletteHTTPException, http_exception_handler)
app.add_exception_handler(Exception, global_exception_handler)

# Middleware
allowed_origins = [settings.frontend_origin] if settings.frontend_origin else ["*"]
if settings.env in ("development", "test") or not settings.frontend_origin:
    allowed_origins = ["*"]

app.add_middleware(
    CORSMiddleware,
    allow_origins=allowed_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
app.add_middleware(LoggingMiddleware)

# Routes
app.include_router(health.router)
app.include_router(internal.router)
app.include_router(chat.router)
app.include_router(models.router)


@app.get("/")
async def root():
    return {"status": "ok", "version": settings.version, "environment": settings.env}
