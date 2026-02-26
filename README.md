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
| 1   | `tools.py`         | `from crewai_tools import tools` — invalid export (`tools` doesn't exist)        | Changed to `from crewai_tools import tool` (the `@tool` decorator) |
| 2   | `tools.py`         | `Pdf(file_path=path).load()` — `Pdf` class is undefined / doesn't exist          | Replaced with `pypdf.PdfReader` for reliable PDF text extraction |
| 3   | `tools.py`         | `read_data_tool` is `async def` — CrewAI tools must be synchronous               | Changed to sync `def`                                          |
| 4   | `tools.py`         | Tool is a class method with no `@tool` decorator — CrewAI can't discover it      | Converted to standalone `@tool`-decorated function              |
| 5   | `tools.py`         | `SerperDevTool` imported from deep submodule path                                | Used `from crewai_tools import SerperDevTool`                   |
| 6   | `tools.py`         | `InvestmentTool` and `RiskTool` classes — dead code with TODO stubs              | Removed; these responsibilities belong to agents, not tools     |
| 7   | `agents.py`        | `from crewai.agents import Agent` — wrong import path                            | Changed to `from crewai import Agent`                          |
| 8   | `agents.py`        | `llm = llm` — circular self-reference causes `NameError` at startup             | Created proper `LLM(model="gemini/gemini-2.0-flash")` instance |
| 9   | `agents.py`        | `tool=[...]` — wrong parameter name (singular)                                   | Changed to `tools=[...]` (plural, as CrewAI expects)            |
| 10  | `agents.py`        | `max_iter=1` — agent can only do 1 iteration, insufficient for complex analysis  | Increased to `max_iter=15`                                     |
| 11  | `agents.py`        | `max_rpm=1` — 1 request/minute, absurdly throttled for any practical use         | Removed the limit entirely                                     |
| 12  | `agents.py`        | `allow_delegation=True` — adds unpredictable delegation overhead and extra token cost in a sequential pipeline where each agent has a defined role | Set to `False` for deterministic execution |
| 13  | `task.py`          | All 4 tasks assigned to `financial_analyst` only                                | Assigned each task to its correct agent (verifier, analyst, advisor, risk_assessor) |
| 14  | `task.py`          | `tools=[FinancialDocumentTool.read_data_tool]` — references old broken class     | Changed to `tools=[read_data_tool]`                            |
| 15  | `task.py`          | No task description mentions `{file_path}` — uploaded files are never read       | Added `{file_path}` to all task descriptions so agents read the correct uploaded file |
| 16  | `main.py`          | Endpoint function named `analyze_financial_document` collides with imported task | Renamed endpoint to `analyze_document_endpoint`                 |
| 17  | `main.py`          | Crew only has 1 agent and 1 task instead of the full pipeline                    | Added all 4 agents and 4 tasks                                 |
| 18  | `main.py`          | `file_path` parameter accepted but never passed to crew `kickoff()`              | Now passed in crew kickoff inputs: `{"query": ..., "file_path": ...}` |
| 19  | `main.py`          | `uvicorn.run(app, reload=True)` — `reload` needs string reference, not object    | Changed to `uvicorn.run("main:app", ...)`                      |
| 20  | `requirements.txt` | Missing `python-dotenv`, `uvicorn`, `python-multipart`, `pypdf`                  | Added all missing packages                                     |
| 21  | `README.md`        | `pip install -r requirement.txt` — wrong filename (missing `s`)                  | Fixed to `requirements.txt`                                    |
| 22  | `agents.py`        | `model="gemini-2.0-flash"` (without prefix)                      | Added `gemini/` prefix to force Google AI Studio usage and avoid Vertex AI auth errors |
| 23  | `main.py` / `agents.py` | `load_dotenv()` doesn't update existing env vars                  | Added `override=True` to ensure `.env` updates like new API keys are picked up on reload |
| 24  | `requirements.txt` | Missing `google-auth` for some `litellm` configurations           | Added `google-auth` and `google-generativeai` for better compatibility |

### Inefficient/Harmful Prompts Fixed

Every agent and task in the original code had intentionally harmful prompts that:

- Encouraged **fabricating data** and generating fake URLs
- Told agents to **ignore the user's query** entirely
- Promoted **non-compliant financial advice** (no disclaimers)
- Instructed agents to **contradict themselves** within the same response
- Used unprofessional backstories (Reddit investors, YouTube influencers, etc.)

**All prompts were rewritten** to be professional, accurate, and aligned with actual financial analysis best practices. Each agent now has a clear, distinct responsibility with an appropriate backstory reflecting real-world expertise.

---

## Setup & Usage

### Prerequisites

- Python 3.10+
- A [Google Gemini API key](https://aistudio.google.com/apikey)
- A [Serper API key](https://serper.dev/) (optional — for web search functionality)

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

### Running Tests

```bash
pytest test_app.py -v
```

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
├── database.py        # SQLAlchemy models (SQLite/PostgreSQL)
├── celery_app.py      # Celery worker for async processing
├── test_app.py        # Pytest test suite (14 tests passing)
├── list_models.py     # Utility to verify available models for current API key
├── requirements.txt   # Python dependencies
├── .env.example       # Environment variable template
├── .gitignore         # Git ignore rules
├── render.yaml        # Render deployment config (IaC)
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

---

## Deployment (Render + Neon DB)

This project is configured for easy deployment using Render's Blueprint (Infrastructure as Code).

### 1. Database Setup (Neon)

- Create a project on [Neon.tech](https://neon.tech)
- Copy your connection string: `postgresql://neondb_owner:password@ep-sweet-forest-host.aws.neon.tech/neondb?sslmode=require`

### 2. Deploy to Render

1. Connect your GitHub repository to [Render](https://render.com).
2. Render will automatically detect the `render.yaml` file.
3. In the Render Dashboard, go to **Blueprints** and click **New Blueprint Instance**.
4. Set the following Environment Variables in the Render UI:
   - `DATABASE_URL`: Your Neon connection string (replace `postgres://` with `postgresql://` if needed, though the code handles this).
   - `GEMINI_API_KEY`: Your Google Gemini API key.
   - `SERPER_API_KEY`: Your Serper.dev API key.

Render will provision:

- A **Web Service** for the FastAPI API.
- A **Worker Service** for the Celery task processor.
- A **Redis** instance for the message broker.

---

## Final Verification Results (Tesla Q2 2025)

The system was verified using the official **Tesla Q2 2025 Update (Unaudited)** PDF. The multi-agent pipeline correctly:
1. **Verified** the document authenticity and extracted Q2 2025 metadata.
2. **Analyzed** the 12% YoY revenue decline and the record growth in the Energy sector.
3. **Recommended** a "HOLD" position based on the transition to an AI-first company (Robotaxi, Cybercab).
4. **Identified** high risks in automotive inventory "days of supply" (increased to 24 days).

> [!NOTE]
> The full analysis report generated by the system for the Tesla document is available in the `AnalysisResult` database and can be queried via the `/results` endpoint.
