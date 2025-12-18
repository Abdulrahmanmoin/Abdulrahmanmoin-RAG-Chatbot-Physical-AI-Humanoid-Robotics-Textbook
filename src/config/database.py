from sqlalchemy import create_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
from pydantic_settings import BaseSettings
from pydantic import Field
# import os

class Settings(BaseSettings):
    # database_url: str = os.getenv("NEON_DATABASE_URL", "")
    database_url: str = Field(default="", alias="NEON_DATABASE_URL")

    class Config:
        env_file = ".env"
        extra = "ignore"

settings = Settings()

# Create the database engine
engine = create_engine(
    settings.database_url,
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