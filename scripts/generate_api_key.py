#!/usr/bin/env python3
"""
API Key Generation Script for Sentilyzer Platform

This script generates secure API keys for users and stores them in the database.
Phase 2 Implementation: Production-ready user and API key management.
"""

import hashlib
import os
import secrets
import string
import sys
from datetime import datetime, timedelta
from typing import Optional
from uuid import uuid4

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

# Add common module to path
sys.path.append(os.path.join(os.path.dirname(__file__), "../common"))

try:
    import bcrypt
    from sqlalchemy.orm import Session

    from app.db.models import ApiKey, User
    from app.db.session import create_session, get_db_engine
except ImportError as e:
    print(f"❌ Error importing required modules: {e}")
    print("Make sure you're running this from the project root directory.")
    sys.exit(1)


def generate_api_key(email: str) -> str:
    """Generate a new API key for a user."""
    # Database configuration
    DATABASE_URL = os.getenv(
        "DATABASE_URL", "postgresql://postgres:postgres@localhost:5432/sentilyzer"
    )

    # Create database engine and session
    engine = create_engine(DATABASE_URL)
    SessionLocal = sessionmaker(bind=engine)
    session = SessionLocal()

    try:
        # Check if user exists
        user = session.query(User).filter(User.email == email).first()
        if not user:
            print("Error: User not found")
            return ""

        # Generate new API key
        api_key = str(uuid4())

        # Create API key record
        new_key = ApiKey(
            key=api_key, user_id=user.id, created_at=datetime.utcnow(), is_active=True
        )

        # Save to database
        session.add(new_key)
        session.commit()

        print("Successfully generated API key")
        print("API Key:", api_key)

        return api_key

    except Exception as e:
        print("Error generating API key:", str(e))
        return ""

    finally:
        session.close()


def hash_api_key(api_key: str) -> str:
    """
    Hash an API key using SHA-256 for database storage.
    We use SHA-256 for API keys as they are meant to be compared frequently.
    """
    return hashlib.sha256(api_key.encode()).hexdigest()


def hash_password(password: str) -> str:
    """
    Hash a password using bcrypt for secure storage.
    """
    return bcrypt.hashpw(password.encode("utf-8"), bcrypt.gensalt()).decode("utf-8")


def create_user_and_api_key(
    email: str, password: str, expires_in_days: Optional[int] = None
) -> tuple[User, ApiKey, str]:
    """
    Create a new user and associated API key in the database.

    Returns:
        tuple: (user, api_key_record, raw_api_key)
    """
    try:
        # Create database session
        session = create_session()

        # Check if user already exists
        existing_user = session.query(User).filter(User.email == email).first()
        if existing_user:
            raise ValueError(f"User with email {email} already exists")

        # Create new user
        hashed_password = hash_password(password)
        user = User(email=email, hashed_password=hashed_password, is_active=True)
        session.add(user)
        session.flush()  # Get the user ID

        # Generate API key
        raw_api_key = generate_api_key(email)
        key_hash = hash_api_key(raw_api_key)

        # Calculate expiration date
        expires_at = None
        if expires_in_days:
            expires_at = datetime.utcnow() + timedelta(days=expires_in_days)

        # Create API key record
        api_key_record = ApiKey(
            key_hash=key_hash, user_id=user.id, is_active=True, expires_at=expires_at
        )
        session.add(api_key_record)

        # Commit transaction
        session.commit()

        return user, api_key_record, raw_api_key

    except Exception as e:
        session.rollback()
        raise e
    finally:
        session.close()


def main():
    """
    Interactive API key generation with user creation.
    """
    print("🔑 Sentilyzer API Key Generator (Phase 2)")
    print("=" * 50)
    print()

    try:
        # Get user input
        email = input("Enter user email: ").strip()
        if not email or "@" not in email:
            print("❌ Please provide a valid email address.")
            return

        password = input("Enter user password: ").strip()
        if len(password) < 8:
            print("❌ Password must be at least 8 characters long.")
            return

        expires_input = input(
            "API key expiration (days, blank for no expiration): "
        ).strip()
        expires_in_days = None
        if expires_input:
            try:
                expires_in_days = int(expires_input)
                if expires_in_days <= 0:
                    print("❌ Expiration days must be positive.")
                    return
            except ValueError:
                print("❌ Please enter a valid number of days.")
                return

        print()
        print("Creating user and generating API key...")

        # Create user and API key
        user, api_key_record, raw_api_key = create_user_and_api_key(
            email=email, password=password, expires_in_days=expires_in_days
        )

        print()
        print("✅ SUCCESS!")
        print("-" * 30)
        print(f"👤 User Created:")
        print(f"   Email: {user.email}")
        print(f"   User ID: {user.id}")
        print(f"   Created: {user.created_at}")
        print()
        print(f"🔑 API Key Generated:")
        print(f"   Key: {raw_api_key}")
        print(f"   Expires: {api_key_record.expires_at or 'Never'}")
        print()
        print("⚠️  IMPORTANT SECURITY NOTES:")
        print("   - This API key will NOT be shown again")
        print("   - Store it securely (password manager recommended)")
        print("   - Use it in Authorization header: Bearer <key>")
        print(
            f"   - Test with: curl -H 'Authorization: Bearer {raw_api_key}' <api_url>"
        )
        print()
        print("🎯 Next Steps:")
        print("   1. Save the API key securely")
        print("   2. Test authentication with /v1/signals endpoint")
        print("   3. Monitor usage in application logs")

    except ValueError as e:
        print(f"❌ Error: {e}")
    except Exception as e:
        print(f"❌ Database error: {e}")
        print("Make sure the database is running and migrations are applied.")


if __name__ == "__main__":
    if len(sys.argv) != 2:
        print("Usage: python generate_api_key.py <email>")
        sys.exit(1)

    email = sys.argv[1]
    generate_api_key(email)
