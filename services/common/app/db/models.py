import uuid
from datetime import datetime

from sqlalchemy import (JSON, Boolean, Column, DateTime, Float, ForeignKey,
                        Integer, String, Text)
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship

from .base import Base


class User(Base):
    """User model."""

    __tablename__ = "users"

    id = Column(Integer, primary_key=True)
    email = Column(String(255), unique=True, nullable=False)
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime, default=datetime.utcnow)

    # Relationships
    api_keys = relationship("ApiKey", back_populates="user")
    articles = relationship("RawArticle", back_populates="user")

    def __repr__(self):
        return (
            f"<User(id={self.id}, email='{self.email}', "
            f"is_active={self.is_active}, created_at='{self.created_at}')>"
        )


class ApiKey(Base):
    """API key model."""

    __tablename__ = "api_keys"

    id = Column(Integer, primary_key=True)
    key = Column(String(255), unique=True, nullable=False)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow)
    is_active = Column(Boolean, default=True)

    # Relationships
    user = relationship("User", back_populates="api_keys")

    def __repr__(self):
        return (
            f"<ApiKey(id={self.id}, user_id={self.user_id}, "
            f"is_active={self.is_active}, created_at='{self.created_at}')>"
        )


class RawArticle(Base):
    """Raw article model."""

    __tablename__ = "raw_articles"

    id = Column(Integer, primary_key=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    source = Column(String(255), nullable=False)
    content = Column(Text, nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow)
    processed = Column(Boolean, default=False)
    has_error = Column(Boolean, default=False)

    # Relationships
    user = relationship("User", back_populates="articles")
    sentiment_scores = relationship("SentimentScore", back_populates="article")

    def __repr__(self):
        return (
            f"<RawArticle(id={self.id}, source='{self.source}', "
            f"content='{self.content}', created_at='{self.created_at}')>"
        )


class SentimentScore(Base):
    """Sentiment score model."""

    __tablename__ = "sentiment_scores"

    id = Column(Integer, primary_key=True)
    article_id = Column(Integer, ForeignKey("raw_articles.id"), nullable=False)
    sentiment_score = Column(Float, nullable=False)
    sentiment_label = Column(String(50), nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow)

    # Relationships
    article = relationship("RawArticle", back_populates="sentiment_scores")

    def __repr__(self):
        return (
            f"<SentimentScore(id={self.id}, article_id={self.article_id}, "
            f"score={self.sentiment_score}, label='{self.sentiment_label}')>"
        )
