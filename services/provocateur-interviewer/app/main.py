import asyncio
from contextlib import asynccontextmanager
from fastapi import FastAPI
from app.realtime.interviewer import router as interview_router
from app.background.provocateur import start_worker

@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup: Initialize resources
    print("Starting Provocateur-Interviewer Service...")
    asyncio.create_task(start_worker())
    yield
    # Shutdown: Cleanup resources
    print("Shutting down Provocateur-Interviewer Service...")

app = FastAPI(
    title="The Provocateur & Interviewer",
    lifespan=lifespan
)

@app.get("/health")
async def health_check():
    return {"status": "ok"}

app.include_router(interview_router, prefix="/api/v1")
