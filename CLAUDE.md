# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

REST API for an automated multi-agent job search and application generation system, deployed on HuggingFace Spaces. The system searches for relevant job postings and automatically generates customized CVs and motivation letters for each position.

Target: English-speaking trainer, learning designer, and experiential learning designer positions in the Netherlands for name surname.

**Key difference from typical workflows**: This is an **API-triggered** system, not a scheduled/cron system. Workflows execute on-demand via HTTP requests.

## Development Commands

### Setup
```bash
# Create virtual environment
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt

# Configure environment
cp .env.example .env
# Edit .env and add your OPENAI_API_KEY
```

### Running the Application
```bash
# Start API server
python app.py

# Or use uvicorn directly with auto-reload
uvicorn app:app --reload --port 7860

# Test the API
curl -X POST http://localhost:7860/api/trigger
curl http://localhost:7860/health
```

### Testing Workflow Directly
```bash
# For debugging, you can still run workflow.py directly
python workflow.py --once
```

## Architecture

### API-First Multi-Agent System

This project uses a **REST API + Background Tasks** pattern:

```
External Request (HTTP POST)
    ↓
FastAPI Endpoint (/api/trigger)
    ↓
Background Task (non-blocking)
    ↓
JobApplicationWorkflow.run_once_for_api()
    ↓
Sequential Agent Execution:
  1. JobFinderAgent → Search jobs
  2. ApplicationWriterAgent → Generate materials (for each job)
    ↓
Results stored in job_status_store (in-memory)
    ↓
Client polls /api/status/{job_id}
    ↓
Client retrieves results via /api/results/{job_id}
```

### Key Components

**FastAPI Application** ([app.py](app.py)):
- Main entry point for the API
- Defines all REST endpoints
- Manages `job_status_store` (in-memory dict for job tracking)
- Uses `BackgroundTasks` for async workflow execution
- Returns immediately with `job_id` for status polling

**Workflow Orchestrator** ([workflow.py](workflow.py)):
- `JobApplicationWorkflow` class coordinates agent execution
- `run_once_for_api()` - API-compatible method that returns structured dict (no console printing)
- `run_daily_workflow()` - CLI-compatible method with console output
- `run_scheduled()` - Optional scheduled mode (requires `schedule` library, not used in HF Spaces)

**Agent Base Class** ([agents/base_agent.py](agents/base_agent.py)):
- All agents inherit from `BaseAgent`
- Provides OpenAI API client initialization
- Standard `run(input_data) → output_data` interface
- Each agent implements `_execute()` method
- Built-in error handling and execution logging

**JobFinderAgent** ([agents/job_finder_agent.py](agents/job_finder_agent.py)):
- Uses GPT-4 to simulate job search (placeholder for real API integration)
- Structured prompt engineering to generate realistic job postings
- Saves results to `storage/job_postings/YYYY-MM-DD.json`
- Returns list of job posting dictionaries

**ApplicationWriterAgent** ([agents/application_writer_agent.py](agents/application_writer_agent.py)):
- Loads templates from `templates/` directory
- Uses GPT-4 to customize CV and motivation letter for each job
- Generates match analysis summary (strengths/gaps/recommendations)
- Saves outputs to `storage/applications/YYYY-MM-DD/company_name/`

**Configuration** ([config/settings.py](config/settings.py)):
- Loads environment variables via `python-dotenv`
- `USER_PROFILE` dict with job seeker information
- File paths using `pathlib.Path`
- Auto-creates storage directories on import

### API Endpoints

| Endpoint | Method | Purpose |
|----------|--------|---------|
| `/` | GET | API information |
| `/health` | GET | Health check |
| `/api/trigger` | POST | Start workflow (returns job_id) |
| `/api/status/{job_id}` | GET | Check execution status |
| `/api/results/{job_id}` | GET | Get full results (when completed) |
| `/api/jobs` | GET | List all jobs |
| `/api/cleanup/{job_id}` | DELETE | Remove job from store |

### Data Flow

```
HTTP POST /api/trigger
    ↓
Generate job_id (UUID)
    ↓
Initialize job in job_status_store
{
  "job_id": "...",
  "status": "pending",
  "created_at": "..."
}
    ↓
Start BackgroundTask: run_workflow_task(job_id)
    ↓
Update status to "running"
    ↓
Execute workflow.run_once_for_api()
    ├─ JobFinderAgent searches jobs
    ├─ ApplicationWriterAgent processes each job
    └─ Returns structured results dict
    ↓
Update job_status_store with results
{
  "status": "completed",
  "jobs_found": 5,
  "applications_generated": 5,
  "results": {...}
}
```

### Storage Structure

```
storage/
├── job_postings/          # Daily search results
│   └── YYYY-MM-DD.json    # All postings for that day
└── applications/          # Generated materials
    └── YYYY-MM-DD/        # Organized by date
        └── company_name/  # One folder per company
            ├── customized_cv_company_name.md
            ├── motivation_letter_company_name.md
            └── match_summary_company_name.md
```

**Important**: On HuggingFace Spaces, `storage/` is **ephemeral** (lost on restart). Results are returned via API, not persisted long-term.

## Important Implementation Notes

### API vs. CLI Mode

The workflow supports both modes:

1. **API Mode** (default for HF Spaces):
   - Triggered via `POST /api/trigger`
   - Uses `workflow.run_once_for_api()` → returns dict
   - No console output, structured results only
   - Background task execution

2. **CLI Mode** (for local development/testing):
   - Run `python workflow.py --once`
   - Uses `workflow.run_daily_workflow()` → prints to console
   - Direct execution, synchronous

### Background Task Execution

FastAPI's `BackgroundTasks` runs workflow after response is sent:

```python
@app.post("/api/trigger")
async def trigger_workflow(background_tasks: BackgroundTasks):
    job_id = str(uuid.uuid4())
    job_status_store[job_id] = {"status": "pending", ...}

    # This runs AFTER the response is returned
    background_tasks.add_task(run_workflow_task, job_id)

    return {"job_id": job_id, "status": "pending"}
```

### In-Memory State Management

`job_status_store` is a **dict in memory**:
- Fast for single-instance deployments
- **Lost on container restart**
- For production: Use Redis, PostgreSQL, or persistent session store

### Environment Variables

Required in `.env` or HuggingFace Spaces Secrets:
- `OPENAI_API_KEY` - Must be valid OpenAI API key starting with `sk-`
- `USER_NAME` - Defaults to "name surname"
- `USER_LOCATION` - Defaults to "Netherlands"

Note: `TIMEZONE` and `SCHEDULE_TIME` are not used in API mode.

### Error Handling

Multi-layer error handling:

1. **Agent level**: `BaseAgent.run()` catches exceptions, returns `{"success": False, "error": "..."}`
2. **Workflow level**: `run_once_for_api()` catches all exceptions, returns error dict
3. **API level**: Background task stores errors in `job_status_store`

Workflow continues processing remaining jobs even if one fails.

### Extending with Real Job APIs

Current `JobFinderAgent._execute()` uses LLM to simulate job searches. To integrate real APIs:

```python
# In agents/job_finder_agent.py
import requests

def _execute(self, input_data):
    # Example: LinkedIn Jobs API
    response = requests.get(
        "https://api.linkedin.com/v2/jobs/search",
        headers={"Authorization": f"Bearer {LINKEDIN_API_KEY}"},
        params={
            "keywords": "Learning Designer",
            "location": "Netherlands"
        }
    )
    job_postings = self._parse_api_response(response.json())

    # Keep the same return structure
    return {
        "success": True,
        "job_postings": job_postings,
        ...
    }
```

### Template Customization

Templates are in [templates/](templates/):
- [base_cv.md](templates/base_cv.md) - CV structure
- [base_motivation_letter.md](templates/base_motivation_letter.md) - Letter template

If templates don't exist, agents use hardcoded defaults in `ApplicationWriterAgent._get_default_template()`.

### Adding New Agents

1. Create new agent class in `agents/` directory
2. Inherit from `BaseAgent`
3. Implement `_execute(input_data) → dict` method
4. Add to workflow in [workflow.py](workflow.py):
   ```python
   self.my_new_agent = MyNewAgent()
   # In run_once_for_api():
   result = self.my_new_agent.run(some_data)
   ```

### Model Configuration

Default model: `gpt-4o` (set in `BaseAgent.__init__()` line 11)

To change globally, edit [agents/base_agent.py](agents/base_agent.py). To change per-agent, pass `model` parameter when instantiating.

## HuggingFace Spaces Deployment

### Configuration

The HF Spaces config is in README frontmatter:
```yaml
---
title: Job Application Flow
emoji: 💼
sdk: docker
---
```

### Secrets

Add in HF Spaces UI (Settings → Repository secrets):
- `OPENAI_API_KEY` - Your OpenAI API key

### Dockerfile

[Dockerfile](Dockerfile) is configured for HF Spaces:
- Port 7860 (HF standard)
- Non-root user for security
- Creates storage directories
- Runs uvicorn server

### Testing After Deployment

```bash
# Replace with your actual HF Space URL
export HF_URL="https://your-username-space-name.hf.space"

# Trigger workflow
curl -X POST $HF_URL/api/trigger

# Get the job_id from response, then:
curl $HF_URL/api/status/{job_id}
curl $HF_URL/api/results/{job_id}
```

## Common Development Tasks

### Add API Authentication

```python
# In app.py
from fastapi import Header, HTTPException

API_KEY = os.getenv("API_KEY", "your-secret-key")

def verify_api_key(x_api_key: str = Header(...)):
    if x_api_key != API_KEY:
        raise HTTPException(status_code=401, detail="Invalid API key")
    return x_api_key

@app.post("/api/trigger", dependencies=[Depends(verify_api_key)])
async def trigger_workflow(background_tasks: BackgroundTasks):
    # ...
```

### Add Rate Limiting

```python
pip install slowapi

from slowapi import Limiter
from slowapi.util import get_remote_address

limiter = Limiter(key_func=get_remote_address)
app.state.limiter = limiter

@app.post("/api/trigger")
@limiter.limit("5/minute")
async def trigger_workflow(request: Request, background_tasks: BackgroundTasks):
    # ...
```

### Add Persistent Storage

```python
# Install Redis
pip install redis

import redis
r = redis.Redis(host='localhost', port=6379, db=0)

# Instead of job_status_store dict:
def save_job_status(job_id, data):
    r.set(f"job:{job_id}", json.dumps(data))

def get_job_status(job_id):
    data = r.get(f"job:{job_id}")
    return json.loads(data) if data else None
```

### Debug Workflow Issues

```python
# Add logging in workflow.py
import logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def run_once_for_api(self):
    logger.info("Starting workflow...")
    try:
        job_search_result = self.job_finder.run({})
        logger.info(f"Found {len(job_search_result.get('job_postings', []))} jobs")
        # ...
    except Exception as e:
        logger.error(f"Workflow failed: {e}", exc_info=True)
        raise
```

## Troubleshooting

### "Import workflow could not be resolved"
- Ensure you're in the correct directory
- Check virtual environment is activated
- Verify all files copied from backend folder

### "OpenAI API key not found"
- Check `.env` file exists with `OPENAI_API_KEY=sk-...`
- On HF Spaces, verify secret is set in Settings

### "Job status not found" after restart
- `job_status_store` is in-memory, lost on restart
- This is expected behavior
- For persistence, implement Redis/database storage

### Long execution times
- Workflow makes multiple OpenAI API calls (1 for job search + N for applications)
- Consider caching, batching, or using faster models for development

## File Organization

```
job_application_flow/
├── app.py                  # FastAPI app, API endpoints
├── workflow.py             # Workflow orchestrator
├── agents/                 # Agent implementations
│   ├── __init__.py
│   ├── base_agent.py       # Base class
│   ├── job_finder_agent.py
│   └── application_writer_agent.py
├── config/
│   ├── __init__.py
│   └── settings.py         # Environment config
├── templates/              # Application templates
│   ├── base_cv.md
│   └── base_motivation_letter.md
├── storage/                # Runtime (gitignored)
│   ├── job_postings/
│   └── applications/
├── requirements.txt        # Dependencies
├── Dockerfile              # HF Spaces config
├── .env.example            # Example env vars
├── .gitignore
├── README.md
└── CLAUDE.md               # This file
```
