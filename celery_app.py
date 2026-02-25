"""Celery worker for asynchronous financial document processing."""

import os
from datetime import datetime

from celery import Celery
from dotenv import load_dotenv

load_dotenv()

# Celery configuration — uses Redis as broker and backend
REDIS_URL = os.getenv("REDIS_URL", "redis://localhost:6379/0")

celery_app = Celery(
    "financial_analyzer",
    broker=REDIS_URL,
    backend=REDIS_URL,
)

celery_app.conf.update(
    task_serializer="json",
    accept_content=["json"],
    result_serializer="json",
    timezone="UTC",
    enable_utc=True,
    task_track_started=True,
    result_expires=3600,  # Results expire after 1 hour
)


@celery_app.task(bind=True, name="analyze_document_task")
def analyze_document_task(self, job_id: str, query: str, file_path: str, filename: str):
    """Celery task to process a financial document asynchronously."""
    from database import SessionLocal, AnalysisResult

    db = SessionLocal()

    try:
        # Update status to processing
        record = db.query(AnalysisResult).filter(AnalysisResult.job_id == job_id).first()
        if record:
            record.status = "processing"
            db.commit()

        # Import here to avoid circular imports
        from crewai import Crew, Process
        from agents import financial_analyst, verifier, investment_advisor, risk_assessor
        from task import (
            analyze_financial_document,
            verification,
            investment_analysis,
            risk_assessment,
        )

        financial_crew = Crew(
            agents=[verifier, financial_analyst, investment_advisor, risk_assessor],
            tasks=[verification, analyze_financial_document, investment_analysis, risk_assessment],
            process=Process.sequential,
            verbose=True,
        )

        result = financial_crew.kickoff({"query": query, "file_path": file_path})

        # Update database with result
        if record:
            record.status = "success"
            record.result = str(result)
            record.completed_at = datetime.utcnow()
            db.commit()

        return {"status": "success", "job_id": job_id, "result": str(result)}

    except Exception as e:
        # Update database with error
        if record:
            record.status = "failed"
            record.error = str(e)
            record.completed_at = datetime.utcnow()
            db.commit()

        return {"status": "failed", "job_id": job_id, "error": str(e)}

    finally:
        db.close()
        # Clean up the uploaded file
        if os.path.exists(file_path):
            try:
                os.remove(file_path)
            except OSError:
                pass
