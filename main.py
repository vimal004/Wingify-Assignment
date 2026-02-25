from fastapi import FastAPI, File, UploadFile, Form, HTTPException, Depends
import os
import uuid
from datetime import datetime

from sqlalchemy.orm import Session

from crewai import Crew, Process
from agents import financial_analyst, verifier, investment_advisor, risk_assessor
from task import (
    analyze_financial_document,
    verification,
    investment_analysis,
    risk_assessment,
)
from database import init_db, get_db, AnalysisResult

app = FastAPI(title="Financial Document Analyzer")

# Initialize database on startup
init_db()


def run_crew(query: str, file_path: str = "data/sample.pdf"):
    """Run the full financial analysis crew pipeline."""
    financial_crew = Crew(
        agents=[verifier, financial_analyst, investment_advisor, risk_assessor],
        tasks=[verification, analyze_financial_document, investment_analysis, risk_assessment],
        process=Process.sequential,
        verbose=True,
    )

    result = financial_crew.kickoff({"query": query, "file_path": file_path})
    return result


@app.get("/")
async def root():
    """Health check endpoint"""
    return {"message": "Financial Document Analyzer API is running"}


@app.post("/analyze")
async def analyze_document_endpoint(
    file: UploadFile = File(...),
    query: str = Form(default="Analyze this financial document for investment insights"),
    db: Session = Depends(get_db),
):
    """Analyze financial document synchronously and return results."""

    file_id = str(uuid.uuid4())
    file_path = f"data/financial_document_{file_id}.pdf"

    try:
        # Ensure data directory exists
        os.makedirs("data", exist_ok=True)

        # Save uploaded file
        with open(file_path, "wb") as f:
            content = await file.read()
            f.write(content)

        # Validate query
        if not query or not query.strip():
            query = "Analyze this financial document for investment insights"

        # Process the financial document with all analysts
        response = run_crew(query=query.strip(), file_path=file_path)

        # Save result to database
        db_record = AnalysisResult(
            job_id=file_id,
            filename=file.filename,
            query=query,
            status="success",
            result=str(response),
            completed_at=datetime.utcnow(),
        )
        db.add(db_record)
        db.commit()

        return {
            "status": "success",
            "job_id": file_id,
            "query": query,
            "analysis": str(response),
            "file_processed": file.filename,
        }

    except Exception as e:
        # Save error to database
        db_record = AnalysisResult(
            job_id=file_id,
            filename=file.filename if file else "unknown",
            query=query,
            status="failed",
            error=str(e),
            completed_at=datetime.utcnow(),
        )
        db.add(db_record)
        db.commit()

        raise HTTPException(
            status_code=500,
            detail=f"Error processing financial document: {str(e)}",
        )

    finally:
        # Clean up uploaded file
        if os.path.exists(file_path):
            try:
                os.remove(file_path)
            except OSError:
                pass


@app.post("/analyze/async")
async def analyze_document_async_endpoint(
    file: UploadFile = File(...),
    query: str = Form(default="Analyze this financial document for investment insights"),
    db: Session = Depends(get_db),
):
    """Submit a financial document for asynchronous analysis. Returns a job ID to poll for results."""

    file_id = str(uuid.uuid4())
    file_path = f"data/financial_document_{file_id}.pdf"

    try:
        os.makedirs("data", exist_ok=True)

        with open(file_path, "wb") as f:
            content = await file.read()
            f.write(content)

        if not query or not query.strip():
            query = "Analyze this financial document for investment insights"

        # Create database record with pending status
        db_record = AnalysisResult(
            job_id=file_id,
            filename=file.filename,
            query=query,
            status="pending",
        )
        db.add(db_record)
        db.commit()

        # Enqueue the Celery task
        from celery_app import analyze_document_task

        analyze_document_task.delay(
            job_id=file_id,
            query=query.strip(),
            file_path=file_path,
            filename=file.filename,
        )

        return {
            "status": "queued",
            "job_id": file_id,
            "message": "Document submitted for analysis. Poll /results/{job_id} for results.",
        }

    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Error submitting document for analysis: {str(e)}",
        )


@app.get("/results/{job_id}")
async def get_result(job_id: str, db: Session = Depends(get_db)):
    """Get the analysis result for a specific job ID."""

    record = db.query(AnalysisResult).filter(AnalysisResult.job_id == job_id).first()
    if not record:
        raise HTTPException(status_code=404, detail=f"Job {job_id} not found")

    return {
        "job_id": record.job_id,
        "status": record.status,
        "filename": record.filename,
        "query": record.query,
        "result": record.result,
        "error": record.error,
        "created_at": str(record.created_at) if record.created_at else None,
        "completed_at": str(record.completed_at) if record.completed_at else None,
    }


@app.get("/results")
async def list_results(
    skip: int = 0,
    limit: int = 20,
    db: Session = Depends(get_db),
):
    """List all past analysis results with pagination."""

    records = (
        db.query(AnalysisResult)
        .order_by(AnalysisResult.created_at.desc())
        .offset(skip)
        .limit(limit)
        .all()
    )

    return {
        "total": db.query(AnalysisResult).count(),
        "results": [
            {
                "job_id": r.job_id,
                "status": r.status,
                "filename": r.filename,
                "query": r.query,
                "created_at": str(r.created_at) if r.created_at else None,
                "completed_at": str(r.completed_at) if r.completed_at else None,
            }
            for r in records
        ],
    }


if __name__ == "__main__":
    import uvicorn

    uvicorn.run("main:app", host="0.0.0.0", port=8000, reload=True)
