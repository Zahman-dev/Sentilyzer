"""Main module for the Signals API service.

This service provides endpoints for retrieving sentiment signals for stocks.
"""

import hashlib
import os
from datetime import datetime

import uvicorn
from fastapi import Depends, FastAPI, HTTPException, Request, Security, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import Response
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from slowapi import Limiter, _rate_limit_exceeded_handler
from slowapi.errors import RateLimitExceeded
from slowapi.util import get_remote_address
from sqlalchemy import and_, desc, func
from sqlalchemy.orm import Session

from services.common.app.db.models import ApiKey, RawArticle, SentimentScore, User
from services.common.app.db.session import get_db
from services.common.app.logging_config import get_logger
from services.common.app.schemas.sentiment import (
    HealthResponse,
    SentimentData,
    SignalsRequest,
    SignalsResponse,
)

# Configure logging for the service
logger = get_logger(__name__)

# Security
security = HTTPBearer()

# Environment variables
API_HOST = os.getenv("API_HOST", "127.0.0.1")  # Default to localhost for security
API_PORT = int(os.getenv("API_PORT", "8000"))

# Rate limiter setup
limiter = Limiter(key_func=get_remote_address)

# Create FastAPI app
app = FastAPI(
    title="Sentilyzer Signals API",
    description="API for retrieving sentiment signals for stocks",
    version="1.0.0",
    docs_url="/docs",
    redoc_url="/redoc",
)

# Add rate limiting state and handler
app.state.limiter = limiter
@app.exception_handler(RateLimitExceeded)
async def rate_limit_handler(request: Request, exc: RateLimitExceeded) -> Response:
    return _rate_limit_exceeded_handler(request, exc)

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Configure appropriately for production
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Authentication
credentials_exception = HTTPException(
    status_code=status.HTTP_401_UNAUTHORIZED,
    detail="Invalid or expired API key",
    headers={"WWW-Authenticate": "Bearer"},
)


async def get_current_user(
    request: Request,
    token: HTTPAuthorizationCredentials = Security(security),
    db: Session = Depends(get_db),
) -> User:
    """Authenticate user based on API key."""
    try:
        # Extract API key from Bearer token
        api_key = token.credentials

        # Hash the provided key to find it in the database
        key_hash = hashlib.sha256(api_key.encode()).hexdigest()

        # Query for the API key
        api_key_record = (
            db.query(ApiKey)
            .filter(ApiKey.key_hash == key_hash)
            .filter(ApiKey.is_active.is_(True))
            .first()
        )

        if not api_key_record:
            logger.warning(f"Invalid API key used: {api_key[:8]}...")
            raise HTTPException(status_code=401, detail="Invalid or expired API key")

        # Check if API key has an expiration date and if it's expired
        if api_key_record.expires_at is not None and api_key_record.expires_at <= datetime.utcnow():
            logger.warning(f"Expired API key used for user: {api_key_record.user_id}")
            raise HTTPException(status_code=401, detail="API key has expired")

        # Get associated user
        user = (
            db.query(User)
            .filter(User.id == api_key_record.user_id)
            .filter(User.is_active.is_(True))
            .first()
        )

        if not user:
            logger.warning(
                f"API key {api_key_record.id} belongs to a disabled user: {api_key_record.user_id}"
            )
            raise HTTPException(status_code=401, detail="User account is inactive")

        # Store user in request state for rate limiting
        request.state.current_user = user

        logger.info(f"Authenticated user: {user.email}")
        return user

    except HTTPException as e:
        raise e  # Re-raise HTTPException to maintain status code and detail
    except Exception as e:
        logger.error(f"Authentication error: {e!s}")
        raise HTTPException(status_code=500, detail="Authentication service error") from e


@app.get("/health", response_model=HealthResponse)
@limiter.limit("60/minute")
async def health_check(request: Request):
    """Health check endpoint - No authentication required."""
    return HealthResponse(status="ok", timestamp=datetime.utcnow(), version="1.0.0")


@app.post("/v1/signals", response_model=SignalsResponse)
@limiter.limit("50/minute")
async def get_sentiment_signals(
    request: Request,
    signals_request: SignalsRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Get sentiment analysis signals for a given time period.

    This endpoint returns sentiment data (not investment advice) for articles
    published within the specified date range. The data includes sentiment scores
    and labels generated by our analysis models.

    **Important Disclaimer**: This is analytical data only, not investment advice.
    **Authentication**: Requires valid API key in Authorization header.
    """
    try:
        logger.info(
            f"Processing signals request for user: {current_user.email}, ticker: {signals_request.ticker}, dates: {signals_request.start_date} to {signals_request.end_date}"
        )

        # Query for articles with sentiment scores in the date range
        query = (
            db.query(
                RawArticle.article_url,
                RawArticle.headline,
                RawArticle.published_at,
                SentimentScore.sentiment_score,
                SentimentScore.sentiment_label,
            )
            .join(SentimentScore, RawArticle.id == SentimentScore.article_id)
            .filter(
                and_(
                    RawArticle.ticker == signals_request.ticker,
                    RawArticle.published_at >= signals_request.start_date,
                    RawArticle.published_at <= signals_request.end_date,
                    RawArticle.has_error.is_(False),
                )
            )
            .order_by(desc(RawArticle.published_at))
        )

        # Execute query
        results = query.all()

        # Convert to response format
        sentiment_data = []
        for result in results:
            sentiment_data.append(
                SentimentData(
                    article_url=result.article_url,
                    headline=result.headline,
                    published_at=result.published_at,
                    sentiment_score=result.sentiment_score,
                    sentiment_label=result.sentiment_label,
                )
            )

        logger.info(
            f"Returning {len(sentiment_data)} sentiment records for user: {current_user.email}"
        )

        return SignalsResponse(data=sentiment_data, total_count=len(sentiment_data))

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error processing signals request: {e!s}")
        raise HTTPException(
            status_code=500, detail=f"Internal server error: {e!s}"
        ) from e


@app.get("/v1/stats")
@limiter.limit("30/minute")
async def get_stats(
    request: Request,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Get basic statistics about the data in the system.

    **Authentication**: Requires valid API key.
    """
    try:
        logger.info(f"Stats request from user: {current_user.email}")

        # Count total articles
        total_articles = db.query(RawArticle).count()

        # Count processed articles
        processed_articles = (
            db.query(RawArticle).filter(RawArticle.is_processed.is_(True)).count()
        )

        # Count articles with errors
        error_articles = (
            db.query(RawArticle).filter(RawArticle.has_error.is_(True)).count()
        )

        # Get latest article date
        latest_article = (
            db.query(RawArticle).order_by(desc(RawArticle.published_at)).first()
        )

        latest_article_date = latest_article.published_at if latest_article else None

        return {
            "total_articles": total_articles,
            "processed_articles": processed_articles,
            "error_articles": error_articles,
            "latest_article_date": latest_article_date,
            "processing_rate": (
                f"{processed_articles}/{total_articles}" if total_articles > 0 else "0/0"
            ),
        }

    except Exception as e:
        logger.error(f"Error getting stats: {e!s}")
        raise HTTPException(
            status_code=500, detail=f"Internal server error: {e!s}"
        ) from e


@app.get("/v1/sources")
@limiter.limit("30/minute")
async def get_sources(
    request: Request,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Get available data sources and their article counts.

    **Authentication**: Requires valid API key.
    """
    try:
        logger.info(f"Sources request from user: {current_user.email}")

        # Get source statistics
        sources_query = (
            db.query(
                RawArticle.source,
                func.count(RawArticle.id).label("article_count"),
                func.max(RawArticle.published_at).label("latest_article"),
            )
            .group_by(RawArticle.source)
            .all()
        )

        sources = []
        for source_data in sources_query:
            sources.append(
                {
                    "source": source_data.source,
                    "article_count": source_data.article_count,
                    "latest_article": source_data.latest_article,
                }
            )

        return {"sources": sources, "total_sources": len(sources)}

    except Exception as e:
        logger.error(f"Error getting sources: {e!s}")
        raise HTTPException(
            status_code=500, detail=f"Internal server error: {e!s}"
        ) from e


if __name__ == "__main__":
    logger.info("Starting Signals API Service")
    uvicorn.run(
        "main:app",
        host=API_HOST,
        port=API_PORT,
        reload=True,
        log_level="info"
    )
