import logging
import os
from sqlalchemy import create_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
from .settings import settings

# Set up logging
logger = logging.getLogger(__name__)

# Validate database URL
db_url = settings.database_url
if not db_url:
    # Check if it's in os.environ directly as a fallback
    db_url = os.getenv("NEON_DATABASE_URL", "")

if not db_url:
    logger.error("NEON_DATABASE_URL is not set! Database connection will fail.")
    # Provide a more descriptive error for the user
    raise ValueError(
        "NEON_DATABASE_URL environment variable is missing. "
        "Please set this in your Hugging Face Space secrets or .env file."
    )

# SQLAlchemy 1.4+ and 2.0 require 'postgresql://' instead of 'postgres://'
if db_url.startswith("postgres://"):
    db_url = db_url.replace("postgres://", "postgresql://", 1)

# Create the database engine
engine = create_engine(
    db_url,
    pool_size=20,  # Number of connection objects to keep in the pool
    max_overflow=30,  # Number of connections that can be created beyond pool_size
    pool_pre_ping=True,  # Verify connections before using them
    pool_recycle=300,  # Recycle connections after 5 minutes
)

# Create a configured "SessionLocal" class
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

# Create a Base class for declarative models
Base = declarative_base()

def get_db():
    """Dependency to get database session"""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()