import time
from fastapi import APIRouter, Depends
from app.schemas.health import HealthResponse
from app.config.settings import get_settings, Settings
from app.db.mongo import MongoDBManager

router = APIRouter(tags=["health"])
START_TIME = time.time()

async def get_db_health():
    db_info = {
        "db_connected": False,
        "db_name": None,
        "db_status": "disconnected",
        "db_ping_latency": None,
        "db_collection_count": None
    }
    
    if MongoDBManager.client and MongoDBManager.db is not None:
        try:
            start = time.time()
            await MongoDBManager.client.admin.command('ping')
            db_info["db_ping_latency"] = round((time.time() - start) * 1000, 2)
            db_info["db_connected"] = True
            db_info["db_name"] = MongoDBManager.db.name
            db_info["db_status"] = "connected"
            collections = await MongoDBManager.db.list_collection_names()
            db_info["db_collection_count"] = len(collections)
        except Exception:
            db_info["db_status"] = "error"
            
    return db_info

@router.get("/health", response_model=HealthResponse)
async def health_check(settings: Settings = Depends(get_settings)):
    db_info = await get_db_health()
    return HealthResponse(
        status="healthy",
        version=settings.version,
        uptime=time.time() - START_TIME,
        environment=settings.env,
        **db_info
    )

@router.get("/health/ready", response_model=HealthResponse)
async def health_ready(settings: Settings = Depends(get_settings)):
    db_info = await get_db_health()
    return HealthResponse(
        status="ready" if db_info["db_connected"] else "not_ready",
        version=settings.version,
        uptime=time.time() - START_TIME,
        environment=settings.env,
        **db_info
    )

@router.get("/version")
async def version(settings: Settings = Depends(get_settings)):
    return {"version": settings.version}
