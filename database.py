"""Database integration for storing analysis results using SQLite + SQLAlchemy."""

import os
from datetime import datetime

from sqlalchemy import create_engine, Column, Integer, String, Text, DateTime
from sqlalchemy.orm import sessionmaker, DeclarativeBase

# Database setup - Supports SQLite (local) and PostgreSQL (Neon/Render)
DATABASE_URL = os.getenv("DATABASE_URL")

# Default to SQLite if no URL is provided
if not DATABASE_URL:
    DATABASE_URL = "sqlite:///./financial_analyzer.db"
# Render/Neon often use 'postgres://', but SQLAlchemy requires 'postgresql://'
elif DATABASE_URL.startswith("postgres://"):
    DATABASE_URL = DATABASE_URL.replace("postgres://", "postgresql://", 1)

# Configure engine - SQLite needs check_same_thread=False, Postgres does not
engine_kwargs = {}
if DATABASE_URL.startswith("sqlite"):
    engine_kwargs["connect_args"] = {"check_same_thread": False}

engine = create_engine(DATABASE_URL, **engine_kwargs)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


class Base(DeclarativeBase):
    pass


class AnalysisResult(Base):
    """Model for storing financial document analysis results."""

    __tablename__ = "analysis_results"

    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    job_id = Column(String(36), unique=True, index=True, nullable=False)
    filename = Column(String(255), nullable=False)
    query = Column(Text, nullable=False)
    status = Column(String(20), nullable=False, default="pending")  # pending | processing | success | failed
    result = Column(Text, nullable=True)
    error = Column(Text, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    completed_at = Column(DateTime, nullable=True)


def init_db():
    """Create all database tables."""
    Base.metadata.create_all(bind=engine)


def get_db():
    """Dependency to get a database session."""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
