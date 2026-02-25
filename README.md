# Financial Document Analyzer 📊

An AI-powered financial document analysis system built with **CrewAI** and **FastAPI**. Upload any financial PDF (10-K, 10-Q, earnings reports) and get comprehensive analysis including investment recommendations and risk assessments.

## Architecture

```
┌─────────────┐     ┌─────────────────────────────────────────────┐
│   Client     │────▶│  FastAPI Server (main.py)                   │
│  (REST API)  │◀────│  /analyze  /analyze/async  /results         │
└─────────────┘     └───────┬─────────────┬───────────────────────┘
                            │             │
                    ┌───────▼───────┐ ┌───▼────────────┐
                    │  CrewAI Crew  │ │  Celery Worker  │
                    │  (4 Agents)   │ │  (Redis Queue)  │
                    └───────┬───────┘ └────────────────┘
                            │
         ┌──────────┬───────┼───────────┬──────────────┐
         ▼          ▼       ▼           ▼              ▼
     Verifier   Analyst  Advisor   Risk Assessor   SQLite DB
```

### Agent Pipeline (Sequential)

1. **Verifier** — Validates the document is a legitimate financial report
2. **Financial Analyst** — Extracts key metrics and performs financial analysis
3. **Investment Advisor** — Provides investment recommendations with disclaimers
4. **Risk Assessor** — Evaluates credit, market, operational, and liquidity risks

---

## Bugs Found & Fixed

### Deterministic Code Bugs

| #   | File               | Bug                                                                              | Fix                                                            |
| --- | ------------------ | -------------------------------------------------------------------------------- | -------------------------------------------------------------- |
| 1   | `tools.py`         | `from crewai_tools import tools` — invalid export                                | Changed to `from crewai_tools import tool`                     |
| 2   | `tools.py`         | `Pdf(file_path=path).load()` — `Pdf` class undefined                             | Replaced with `pypdf.PdfReader`                                |
| 3   | `tools.py`         | `read_data_tool` is `async def` — CrewAI tools must be sync                      | Changed to sync `def`                                          |
| 4   | `tools.py`         | Tool is a class method with no decorator — CrewAI won't find it                  | Converted to standalone `@tool` function                       |
| 5   | `tools.py`         | `SerperDevTool` import from deep submodule path                                  | Used `from crewai_tools import SerperDevTool`                  |
| 6   | `agents.py`        | `from crewai.agents import Agent` — wrong import path                            | Changed to `from crewai import Agent`                          |
| 7   | `agents.py`        | `llm = llm` — circular self-reference, `NameError` at startup                    | Created proper `LLM(model="gemini/gemini-2.0-flash")` instance |
| 8   | `agents.py`        | `tool=[...]` — wrong parameter name (singular)                                   | Changed to `tools=[...]` (plural)                              |
| 9   | `agents.py`        | `max_iter=1` — agent can only do 1 iteration, too restrictive                    | Increased to `max_iter=15`                                     |
| 10  | `agents.py`        | `max_rpm=1` — 1 request/minute, absurdly throttled                               | Removed the limit                                              |
| 11  | `agents.py`        | `allow_delegation=True` in single-agent crew — no one to delegate to             | Set to `False`                                                 |
| 12  | `task.py`          | All tasks assigned to `financial_analyst`                                        | Assigned correct agent to each task                            |
| 13  | `task.py`          | `tools=[FinancialDocumentTool.read_data_tool]` — old class reference             | Changed to `tools=[read_data_tool]`                            |
| 14  | `main.py`          | Endpoint function named `analyze_financial_document` collides with imported task | Renamed to `analyze_document_endpoint`                         |
| 15  | `main.py`          | Crew only has 1 agent and 1 task                                                 | Added all 4 agents and 4 tasks                                 |
| 16  | `main.py`          | `file_path` parameter accepted but never passed to crew                          | Now passed in crew kickoff inputs                              |
| 17  | `main.py`          | `uvicorn.run(app, reload=True)` — reload needs string reference                  | Changed to `uvicorn.run("main:app", ...)`                      |
| 18  | `requirements.txt` | Missing `python-dotenv`, `uvicorn`, `python-multipart`, `pypdf`                  | Added all 4 missing packages                                   |
| 19  | `README.md`        | `pip install -r requirement.txt` — wrong filename                                | Fixed to `requirements.txt`                                    |

### Inefficient/Harmful Prompts Fixed

Every agent and task had intentionally harmful prompts that:

- Encouraged **fabricating data** and fake URLs
- Told agents to **ignore the user's query**
- Promoted **non-compliant financial advice**
- Instructed agents to **contradict themselves**

**All prompts were rewritten** to be professional, accurate, and aligned with actual financial analysis best practices. Each agent now has a clear, distinct responsibility with appropriate backstory.

---

## Setup & Usage

### Prerequisites

- Python 3.10+
- A [Google Gemini API key](https://aistudio.google.com/apikey)
- A [Serper API key](https://serper.dev/) (for web search tool)

### Installation

```bash
# Clone the repository
git clone <your-repo-url>
cd financial-document-analyzer-debug

# Create virtual environment
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt

# Configure environment variables
cp .env.example .env
# Edit .env and add your API keys
```

### Running the Server

```bash
uvicorn main:app --host 0.0.0.0 --port 8000 --reload
```

The API will be available at `http://localhost:8000`. Interactive docs at `http://localhost:8000/docs`.

### Optional: Async Processing with Celery

```bash
# Start Redis (requires Redis installed)
redis-server

# Start Celery worker (in a separate terminal)
celery -A celery_app worker --loglevel=info
```

---

## API Documentation

### `GET /` — Health Check

```bash
curl http://localhost:8000/
```

```json
{ "message": "Financial Document Analyzer API is running" }
```

### `POST /analyze` — Synchronous Analysis

Upload a financial PDF and get results immediately.

```bash
curl -X POST http://localhost:8000/analyze \
  -F "file=@data/TSLA-Q2-2025-Update.pdf" \
  -F "query=What are the key financial metrics and growth trends?"
```

**Response:**

```json
{
  "status": "success",
  "job_id": "uuid",
  "query": "What are the key financial metrics and growth trends?",
  "analysis": "...",
  "file_processed": "TSLA-Q2-2025-Update.pdf"
}
```

### `POST /analyze/async` — Async Analysis (Bonus)

Submit a document for background processing. Requires Redis + Celery worker.

```bash
curl -X POST http://localhost:8000/analyze/async \
  -F "file=@data/TSLA-Q2-2025-Update.pdf" \
  -F "query=Perform a full investment analysis"
```

**Response:**

```json
{
  "status": "queued",
  "job_id": "uuid",
  "message": "Document submitted for analysis. Poll /results/{job_id} for results."
}
```

### `GET /results/{job_id}` — Get Analysis Result

```bash
curl http://localhost:8000/results/{job_id}
```

### `GET /results` — List All Results (Bonus)

Paginated list of all past analyses stored in the database.

```bash
curl "http://localhost:8000/results?skip=0&limit=20"
```

---

## Project Structure

```
financial-document-analyzer-debug/
├── main.py            # FastAPI server with all endpoints
├── agents.py          # CrewAI agent definitions (4 agents)
├── task.py            # CrewAI task definitions (4 tasks)
├── tools.py           # PDF reader tool and search tool
├── database.py        # SQLAlchemy models (SQLite)
├── celery_app.py      # Celery worker for async processing
├── requirements.txt   # Python dependencies
├── .env.example       # Environment variable template
├── data/              # Directory for uploaded/sample PDFs
│   └── TSLA-Q2-2025-Update.pdf
└── outputs/           # Output directory
```

## Bonus Features

### 🔄 Queue Worker Model (Celery + Redis)

- `POST /analyze/async` enqueues jobs to a Redis-backed Celery queue
- `GET /results/{job_id}` polls for completion
- Documents are processed in the background by Celery workers
- Supports concurrent request handling

### 🗄️ Database Integration (SQLite + SQLAlchemy)

- Every analysis result is persisted with metadata
- Tracks job status: `pending` → `processing` → `success` / `failed`
- `GET /results` lists all past analyses with pagination
- Easily swappable to PostgreSQL/MySQL via `DATABASE_URL` env var
