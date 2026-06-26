# Agentic Credit Risk Underwriting System

Enterprise-style, multi-agent credit underwriting platform with a FastAPI backend, React frontend, and 11 specialized underwriting agents orchestrated via LangGraph.

## Overview

This project simulates an AI-first underwriting workflow where each stage is handled by a dedicated agent (document intelligence, fraud, income, credit, quantitative risk, compliance, explainability, and more), then consolidated into a final underwriting decision.

Core characteristics:
- 11-agent underwriting pipeline coordinated by `backend/orchestrator.py`
- FastAPI API with async processing and WebSocket progress updates
- React + TypeScript UI with Redux store and analytics views
- Explainability-oriented outputs and structured agent results
- SQLite-by-default local persistence (PostgreSQL-ready configuration)

## Architecture

High-level flow:
1. Client submits a loan application
2. Backend stores request and starts background orchestration
3. Agents run sequentially through the underwriting pipeline
4. Frontend receives real-time status events through WebSocket
5. Final decision and explanations are returned and persisted in memory

Main implementation points:
- Backend entrypoint: `backend/main.py`
- Agent orchestration: `backend/orchestrator.py`
- Agent implementations: `backend/agents/`
- Frontend app: `frontend/src/`

## Repository Structure

```text
ai_Agentic_Credit_Risk/
├── backend/
│   ├── agents/                  # 11 domain agents + Bedrock client
│   ├── main.py                  # FastAPI app and API routes
│   ├── orchestrator.py          # LangGraph-driven orchestration
│   ├── database.py              # SQLAlchemy models/config
│   ├── models.py                # Pydantic request/response models
│   ├── synthetic_data.py        # Synthetic application generation
│   └── test_*.py                # Unit/integration/e2e tests
├── frontend/
│   ├── src/
│   │   ├── pages/               # Home, Application, Decision, Dashboard
│   │   ├── components/
│   │   ├── store/               # Redux slices/store
│   │   └── utils/api.ts         # API client
│   ├── package.json
│   └── vite.config.ts
├── ARCHITECTURE.md
├── QUICKSTART.md
└── README.md
```

## Tech Stack

Backend:
- Python 3.11
- FastAPI + Uvicorn
- LangGraph / LangChain
- XGBoost + SHAP
- SQLAlchemy (SQLite local / PostgreSQL optional)
- AWS SDK (`boto3`) for Bedrock integration

Frontend:
- React 18 + TypeScript
- Redux Toolkit
- Vite
- Tailwind CSS
- Recharts

## Prerequisites

- Python 3.11+
- Node.js 18+
- npm 9+
- (Optional) AWS credentials with Bedrock access for LLM-backed agents

## Setup

### 1. Clone and enter repo

```bash
git clone <your-repo-url>
cd ai_Agentic_Credit_Risk
```

### 2. Backend setup

Windows (PowerShell):

```powershell
cd backend
python -m venv .venv
.\.venv\Scripts\Activate.ps1
pip install -r requirements.txt
```

macOS/Linux:

```bash
cd backend
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
```

Optional environment variables (create `backend/.env`):

```env
AWS_REGION=us-east-1
BEDROCK_MODEL_ID=amazon.nova-pro-v1:0
AWS_ACCESS_KEY_ID=your_access_key
AWS_SECRET_ACCESS_KEY=your_secret_key

# Local DB defaults to SQLite if true
USE_SQLITE=true

# Only used when USE_SQLITE=false
POSTGRES_HOST=localhost
POSTGRES_PORT=5432
POSTGRES_USER=user
POSTGRES_PASSWORD=password
POSTGRES_DB=credit_risk_db
```

Start backend:

```powershell
cd backend
python main.py
```

Backend URLs:
- API base: `http://localhost:8000/api/v1`
- OpenAPI docs: `http://localhost:8000/docs`
- Health: `http://localhost:8000/health`

### 3. Frontend setup

```powershell
cd frontend
npm install
npm run dev
```

Frontend dev URL:
- `http://localhost:3005`

Notes:
- Vite proxy forwards `/api` calls to `http://localhost:8000`
- Frontend can override API URL with `VITE_API_URL`

## API Highlights

System:
- `GET /health`
- `GET /api/v1/agents/status`

Applications:
- `POST /api/v1/applications`
- `GET /api/v1/applications/{application_id}`
- `GET /api/v1/applications/{application_id}/status`
- `GET /api/v1/applications`

Underwriting:
- `POST /api/v1/underwrite/{application_id}`
- `POST /api/v1/underwrite/sync`

Decisions:
- `GET /api/v1/decisions/{application_id}`
- `GET /api/v1/decisions/{application_id}/explanation`

Synthetic/Test Data:
- `GET /api/v1/synthetic/application`
- `POST /api/v1/synthetic/batch`

Analytics:
- `GET /api/v1/analytics/dashboard`
- `GET /api/v1/analytics/agent-performance`

WebSocket:
- `ws://localhost:8000/ws/{application_id}`

## Running Tests

From `backend/`:

```powershell
pytest -q
```

Useful targeted tests:

```powershell
pytest test_agents_unit.py -q
pytest test_e2e_quick.py -q
pytest test_none_safety.py -q
```

## Security and Git Hygiene

This repo ignores common local secrets/artifacts including:
- `.env` and `.env.*`
- virtual environments (`venv`, `.venv`)
- local DB files (`*.db`, `*.sqlite*`)

Before pushing publicly, review repository contents and rotate any accidentally exposed credentials.

## Current Status

- End-to-end backend and frontend structure is present
- Core agent pipeline and API endpoints are implemented
- Test suites are included for unit and e2e validation

## License

No license file is currently included. Add one if you plan to distribute or open source this project.
