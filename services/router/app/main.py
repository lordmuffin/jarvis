from fastapi import FastAPI
from app.core.config import settings
from contextlib import asynccontextmanager
from app.services.observer import observer
from app.api.api import api_router

@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup: Initialize Observer, Check DB, etc.
    print(f"Starting {settings.PROJECT_NAME}...")
    await observer.start()
    yield
    # Shutdown
    print(f"Shutting down {settings.PROJECT_NAME}...")
    await observer.stop()

app = FastAPI(
    title=settings.PROJECT_NAME,
    openapi_url=f"{settings.API_V1_STR}/openapi.json",
    lifespan=lifespan
)

app.include_router(api_router, prefix=settings.API_V1_STR)

@app.get("/health")
async def health_check():
    return {"status": "ok", "service": "intelligent-burst-router"}

@app.get("/")
async def root():
    return {"message": "Welcome to the Jarvis Intelligent Burst Router"}
