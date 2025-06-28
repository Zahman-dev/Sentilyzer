from datetime import date, datetime
from typing import List, Optional

from pydantic import BaseModel, EmailStr, Field


# Request schemas
class SignalsRequest(BaseModel):
    ticker: str = Field(..., description="Stock ticker symbol (e.g., 'AAPL')")
    start_date: date = Field(..., description="Start date for analysis in YYYY-MM-DD format")
    end_date: date = Field(..., description="End date for analysis in YYYY-MM-DD format")


class SentimentAnalysisRequest(BaseModel):
    text: str = Field(..., description="Text to be analyzed for sentiment.")


# Response schemas
class SentimentAnalysisResponse(BaseModel):
    sentiment_score: float = Field(
        ..., ge=-1.0, le=1.0, description="Calculated sentiment score."
    )
    sentiment_label: str = Field(
        ..., description="Sentiment label: positive, negative, or neutral."
    )


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
    data: list[SentimentData]
    total_count: int = Field(..., description="Total number of sentiment records")


# Health check schema
class HealthResponse(BaseModel):
    status: str = Field(..., description="The operational status of the service.")
    timestamp: datetime = Field(..., description="The timestamp of the health check.")
    version: str = Field(..., description="The version of the service.")


# Error schemas
class ErrorDetail(BaseModel):
    message: str
    code: str | None = None


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

    class Config:
        protected_namespaces = ()


class SentimentScoreCreate(SentimentScoreBase):
    article_id: int


class SentimentScore(SentimentScoreBase):
    id: int
    article_id: int
    processed_at: datetime

    class Config:
        from_attributes = True


# User and API Key schemas

# Schemas for User management
class UserBase(BaseModel):
    email: EmailStr = Field(..., description="User's email address")


class UserCreate(UserBase):
    password: str = Field(..., min_length=8, description="User's password (min 8 characters)")


class User(UserBase):
    id: int
    is_active: bool
    created_at: datetime

    class Config:
        from_attributes = True


# Schemas for API Key management
class ApiKeyBase(BaseModel):
    expires_at: datetime | None = Field(None, description="Optional expiration date for the API key")


class ApiKeyCreate(ApiKeyBase):
    pass


class ApiKey(ApiKeyBase):
    id: int
    user_id: int
    is_active: bool
    created_at: datetime

    class Config:
        from_attributes = True


class NewApiKeyResponse(BaseModel):
    api_key: str = Field(..., description="The newly generated API key. This is shown only once.")
    api_key_details: ApiKey


class Signal(BaseModel):
    article_id: int = Field(..., description="The unique identifier for the article.")
    sentiment_score: float = Field(
        ..., description="The calculated sentiment score for the article."
    )

    class Config:
        """Pydantic model configuration."""

        from_attributes = True


class SignalResponse(BaseModel):
    # ... existing code ...
    total_sentiments: int = Field(
        ..., description="The total number of sentiment scores calculated."
    )


class SourceDetail(BaseModel):
    source_name: str = Field(..., description="The name of the data source.")
    article_count: int = Field(..., description="The number of articles from this source.")
    first_article_date: datetime = Field(
        ..., description="The oldest article's publication date from this source."
    )
    last_article_date: datetime = Field(
        ..., description="The newest article's publication date from this source."
    )

    class Config:
        """Pydantic model configuration."""

        from_attributes = True


class SourcesResponse(BaseModel):
    sources: List[SourceDetail] = Field(
        ..., description="A list of available data sources and their details."
    )


class APIKey(BaseModel):
    """Schema for returning a newly created API key (the key itself is only shown once)."""

    key: str = Field(..., description="The API key. This is only returned on creation.")
    user_id: int = Field(..., description="The ID of the user this key belongs to.")
    expires_at: Optional[datetime] = Field(
        default=None, description="The key's expiration date."
    )

    class Config:
        """Pydantic model configuration."""

        from_attributes = True


class APIKeyInfo(BaseModel):
    """Schema for listing API keys, excluding the key itself."""

    id: int = Field(..., description="The unique identifier for the API key.")
    user_id: int = Field(..., description="The ID of the user this key belongs to.")
    is_active: bool = Field(..., description="Whether the API key is currently active.")
    expires_at: Optional[datetime] = Field(
        default=None, description="The key's expiration date."
    )
    created_at: datetime

    class Config:
        """Pydantic model configuration."""

        from_attributes = True
