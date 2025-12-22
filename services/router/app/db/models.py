from sqlalchemy import Column, Integer, String, Float, DateTime
from sqlalchemy.sql import func
from app.db.base import Base

class QueryMetric(Base):
    __tablename__ = "query_metrics"

    id = Column(Integer, primary_key=True, index=True)
    timestamp = Column(DateTime(timezone=True), server_default=func.now())
    provider = Column(String, index=True)  # "lemonade", "gemini", "azure"
    model = Column(String, index=True)
    ttft_ms = Column(Float)  # Time to First Token
    total_latency_ms = Column(Float)
    status = Column(String) # "success", "error"
    error_message = Column(String, nullable=True)
