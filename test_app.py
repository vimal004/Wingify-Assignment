"""Tests for the Financial Document Analyzer API and tools."""

import os
import pytest
from unittest.mock import patch, MagicMock
from fastapi.testclient import TestClient

from main import app
from tools import read_data_tool
from database import init_db, Base, engine


@pytest.fixture(autouse=True)
def setup_test_db():
    """Create a fresh test database for each test."""
    Base.metadata.create_all(bind=engine)
    yield
    Base.metadata.drop_all(bind=engine)


client = TestClient(app)


# ─── Health Check ────────────────────────────────────────────────────────────

class TestHealthCheck:
    def test_root_returns_200(self):
        response = client.get("/")
        assert response.status_code == 200

    def test_root_returns_correct_message(self):
        response = client.get("/")
        data = response.json()
        assert data["message"] == "Financial Document Analyzer API is running"


# ─── PDF Reader Tool ────────────────────────────────────────────────────────

class TestReadDataTool:
    def test_reads_sample_pdf(self):
        """Test that the PDF reader can read the sample document."""
        sample_path = "data/TSLA-Q2-2025-Update.pdf"
        if not os.path.exists(sample_path):
            pytest.skip("Sample PDF not available")

        result = read_data_tool.run(sample_path)
        assert isinstance(result, str)
        assert len(result) > 100  # Should have substantial content

    def test_returns_string(self):
        """Tool should always return a string."""
        sample_path = "data/TSLA-Q2-2025-Update.pdf"
        if not os.path.exists(sample_path):
            pytest.skip("Sample PDF not available")

        result = read_data_tool.run(sample_path)
        assert isinstance(result, str)

    def test_invalid_path_raises(self):
        """Tool should raise an error for non-existent file."""
        with pytest.raises(Exception):
            read_data_tool.run("data/nonexistent_file.pdf")


# ─── Analyze Endpoint ───────────────────────────────────────────────────────

class TestAnalyzeEndpoint:
    def test_analyze_rejects_no_file(self):
        """POST /analyze without a file should return 422."""
        response = client.post("/analyze")
        assert response.status_code == 422

    @patch("main.run_crew")
    def test_analyze_with_file(self, mock_crew):
        """POST /analyze with a valid PDF should return 200."""
        mock_crew.return_value = "Mocked analysis result"

        # Create a minimal test PDF-like file
        test_content = b"%PDF-1.4 test content"
        response = client.post(
            "/analyze",
            files={"file": ("test.pdf", test_content, "application/pdf")},
            data={"query": "Test query"},
        )

        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "success"
        assert data["file_processed"] == "test.pdf"
        assert data["query"] == "Test query"
        assert "analysis" in data
        assert "job_id" in data

    @patch("main.run_crew")
    def test_analyze_default_query(self, mock_crew):
        """POST /analyze without a query should use the default."""
        mock_crew.return_value = "Mocked result"

        response = client.post(
            "/analyze",
            files={"file": ("test.pdf", b"%PDF-1.4 test", "application/pdf")},
        )

        assert response.status_code == 200
        data = response.json()
        assert "Analyze this financial document" in data["query"]


# ─── Results Endpoints ───────────────────────────────────────────────────────

class TestResultsEndpoints:
    def test_results_list_empty(self):
        """GET /results should return empty list initially."""
        response = client.get("/results")
        assert response.status_code == 200
        data = response.json()
        assert data["total"] == 0
        assert data["results"] == []

    def test_results_not_found(self):
        """GET /results/{job_id} with invalid ID should return 404."""
        response = client.get("/results/nonexistent-id")
        assert response.status_code == 404

    @patch("main.run_crew")
    def test_result_stored_after_analysis(self, mock_crew):
        """After a successful analysis, the result should be queryable."""
        mock_crew.return_value = "Stored result"

        # Run an analysis
        analyze_response = client.post(
            "/analyze",
            files={"file": ("test.pdf", b"%PDF-1.4 data", "application/pdf")},
            data={"query": "Store this"},
        )
        job_id = analyze_response.json()["job_id"]

        # Fetch the stored result
        result_response = client.get(f"/results/{job_id}")
        assert result_response.status_code == 200
        data = result_response.json()
        assert data["status"] == "success"
        assert data["filename"] == "test.pdf"

    @patch("main.run_crew")
    def test_results_pagination(self, mock_crew):
        """GET /results should support skip and limit."""
        mock_crew.return_value = "Result"

        # Create 3 analysis records
        for i in range(3):
            client.post(
                "/analyze",
                files={"file": (f"test{i}.pdf", b"%PDF-1.4", "application/pdf")},
            )

        # Fetch with limit
        response = client.get("/results?skip=0&limit=2")
        data = response.json()
        assert data["total"] == 3
        assert len(data["results"]) == 2


# ─── Database Model ─────────────────────────────────────────────────────────

class TestDatabaseModel:
    def test_db_initializes(self):
        """Database should initialize without errors."""
        init_db()  # Should not raise

    def test_analysis_result_fields(self):
        """AnalysisResult model should have all required columns."""
        from database import AnalysisResult

        columns = [c.name for c in AnalysisResult.__table__.columns]
        assert "id" in columns
        assert "job_id" in columns
        assert "filename" in columns
        assert "query" in columns
        assert "status" in columns
        assert "result" in columns
        assert "error" in columns
        assert "created_at" in columns
        assert "completed_at" in columns
