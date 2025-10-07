from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.ext.declarative import declarative_base
import os

# Database URL - update with your PostgreSQL credentials
DATABASE_URL = os.getenv(
    "DATABASE_URL",
    "postgresql://postgres:Harshanya#1@localhost:5432/fincoach_db"
)

# Create engine
engine = create_engine(DATABASE_URL)

# Session maker
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

# Base for models
Base = declarative_base()

def get_db():
    """Dependency for FastAPI routes"""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

def init_db():
    """Initialize database tables"""
    from models import Base  # Import here to avoid circular imports
    Base.metadata.create_all(bind=engine)
    print("✅ Database tables created successfully!")
