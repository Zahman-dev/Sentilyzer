from datetime import datetime
from typing import Optional, List
from pydantic import BaseModel, Field


# Request schemas
class SignalsRequest(BaseModel):
    ticker: str = Field(..., description="Stock ticker symbol (e.g., 'AAPL')")
    start_date: datetime = Field(
        ..., description="Start date for analysis in ISO format"
    )
    end_date: datetime = Field(..., description="End date for analysis in ISO format")


# Response schemas
class SentimentData(BaseModel):
    article_url: str
    headline: str
    published_at: datetime
    sentiment_score: float = Field(
        ..., ge=-1.0, le=1.0, description="Sentiment score between -1 and 1"
    )
    sentiment_label: str = Field(
        ..., description="Sentiment label: positive, negative, or neutral"
    )

    class Config:
        from_attributes = True


class SignalsResponse(BaseModel):
    data: List[SentimentData]
    total_count: int = Field(..., description="Total number of sentiment records")


# Health check schema
class HealthResponse(BaseModel):
    status: str = Field(default="ok")
    timestamp: datetime = Field(default_factory=datetime.utcnow)
    version: str = Field(default="1.0.0")


# Error schemas
class ErrorDetail(BaseModel):
    message: str
    code: Optional[str] = None


class ErrorResponse(BaseModel):
    error: ErrorDetail
    timestamp: datetime = Field(default_factory=datetime.utcnow)


# Database model schemas (for internal use)
class RawArticleBase(BaseModel):
    source: str
    article_url: str
    headline: str
    article_text: str
    published_at: datetime


class RawArticleCreate(RawArticleBase):
    pass


class RawArticle(RawArticleBase):
    id: int
    is_processed: bool
    has_error: bool
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


class SentimentScoreBase(BaseModel):
    sentiment_score: float = Field(..., ge=-1.0, le=1.0)
    sentiment_label: str
    model_version: str = Field(default="placeholder-v1.0")


class SentimentScoreCreate(SentimentScoreBase):
    article_id: int


class SentimentScore(SentimentScoreBase):
    id: int
    article_id: int
    processed_at: datetime

    class Config:
        from_attributes = True
