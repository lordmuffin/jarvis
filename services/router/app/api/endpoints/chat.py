from fastapi import APIRouter, Depends, BackgroundTasks
from sqlalchemy.ext.asyncio import AsyncSession
from app.db.session import get_db
from app.core.router import router_logic
from app.db.models import QueryMetric
import time

router = APIRouter()

@router.post("/completions")
async def chat_completions(
    request: dict, # Simplified for now, should be a Pydantic model compatible with OpenAI API
    background_tasks: BackgroundTasks,
    db: AsyncSession = Depends(get_db)
):
    start_time = time.time()
    model = request.get("model", "default")
    
    # Intelligent Routing Decision
    route = await router_logic.decide_route(db, model)
    
    # Mocking the actual call to Lemonade or Cloud for now
    # In a real impl, we would use httpx to proxy the request
    
    # Simulate processing
    ttft = 0.1 # Mock TTFT
    
    response = {
        "id": "chatcmpl-mock",
        "object": "chat.completion",
        "created": int(time.time()),
        "model": model,
        "choices": [{"index": 0, "message": {"role": "assistant", "content": f"Response from {route}"}}],
        "usage": {"prompt_tokens": 10, "completion_tokens": 10, "total_tokens": 20},
        "system_fingerprint": route
    }
    
    end_time = time.time()
    total_latency = (end_time - start_time) * 1000
    
    # Async Log Metric
    background_tasks.add_task(
        log_metric, db, route, model, ttft * 1000, total_latency, "success"
    )
    
    return response

async def log_metric(db: AsyncSession, provider: str, model: str, ttft: float, latency: float, status: str):
    metric = QueryMetric(
        provider=provider,
        model=model,
        ttft_ms=ttft,
        total_latency_ms=latency,
        status=status
    )
    db.add(metric)
    try:
        await db.commit()
    except Exception as e:
        print(f"Failed to log metric: {e}")
