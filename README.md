---
title: Job Application Flow
emoji: 💼
colorFrom: indigo
colorTo: green
sdk: docker
pinned: false
---

# Job Application Flow API

An automated multi-agent system for job search and application generation, deployed as a REST API on HuggingFace Spaces. This system searches for relevant job postings and automatically generates customized CVs and motivation letters for each position.

## 🚀 Quick Start

```bash
# Trigger the workflow
curl -X POST https://your-space.hf.space/api/trigger

# Response:
{
  "job_id": "abc-123-def-456",
  "status": "pending",
  "message": "Workflow has been queued and will start shortly"
}

# Check status
curl https://your-space.hf.space/api/status/abc-123-def-456

# Get results
curl https://your-space.hf.space/api/results/abc-123-def-456
```

## Overview

This API provides endpoints to trigger an AI-powered workflow that:
1. **Searches** for English-speaking trainer, learning designer, and experiential learning designer roles in the Netherlands
2. **Generates** customized CVs and motivation letters tailored to each job posting
3. **Returns** structured results with match analysis and recommendations

## API Endpoints

### `GET /`
Root endpoint with API information.

### `POST /api/trigger`
Trigger the job search and application generation workflow.

**Response:**
```json
{
  "job_id": "abc-123-def-456",
  "status": "pending",
  "message": "Workflow has been queued and will start shortly",
  "timestamp": "2025-10-23T10:00:00"
}
```

### `GET /api/status/{job_id}`
Check the status of a workflow execution.

**Response:**
```json
{
  "job_id": "abc-123-def-456",
  "status": "completed",
  "jobs_found": 5,
  "applications_generated": 5,
  "started_at": "2025-10-23T10:00:05",
  "completed_at": "2025-10-23T10:02:30"
}
```

**Status values:** `pending`, `running`, `completed`, `failed`

### `GET /api/results/{job_id}`
Get detailed results of a completed workflow.

**Response:**
```json
{
  "job_id": "abc-123-def-456",
  "status": "completed",
  "job_postings": [...],
  "applications": [...],
  "summary": "# Daily Job Search Summary..."
}
```

### `GET /health`
Health check endpoint for monitoring.

### `GET /api/jobs`
List all jobs in the system.

### `DELETE /api/cleanup/{job_id}`
Delete a job from the status store.

## Configuration

### Environment Variables

Set these in HuggingFace Spaces → Settings → Repository secrets:

- **`OPENAI_API_KEY`** (required): Your OpenAI API key
- **`USER_NAME`** (optional): Applicant name (default: "name surname")
- **`USER_LOCATION`** (optional): Location (default: "Netherlands")

### User Profile

The search is configured for:
- **Roles**: Trainer, L&D Specialist, Learning Designer, Experiential Learning Designer
- **Location**: Netherlands
- **Languages**: English, Turkish
- **Job Sources**: LinkedIn, Glassdoor, Indeed (simulated)

To customize, edit `config/settings.py`.

## Local Development

```bash
# Clone and setup
git clone <repo-url>
cd job_application_flow
python -m venv venv
source venv/bin/activate
pip install -r requirements.txt

# Configure
cp .env.example .env
# Edit .env and add your OPENAI_API_KEY

# Run
python app.py
# API available at http://localhost:7860
```

## Architecture

### Multi-Agent System

1. **JobFinderAgent**: Searches for relevant job postings using GPT-4
2. **ApplicationWriterAgent**: Generates customized CVs and motivation letters

### Workflow
```
POST /api/trigger → Background Task → JobFinderAgent → ApplicationWriterAgent → Results
```

## Project Structure

```
job_application_flow/
├── app.py                      # FastAPI application
├── workflow.py                 # Workflow orchestrator
├── agents/                     # AI agents
├── config/                     # Configuration
├── templates/                  # Application templates
├── storage/                    # Generated outputs
├── requirements.txt
├── Dockerfile
└── README.md
```

## Limitations

- Job search is **simulated** (returns realistic but generated postings)
- Storage is **ephemeral** on HuggingFace Spaces (results returned via API)
- Job status stored **in-memory** (lost on restart)

## Support

- Architecture details: See [CLAUDE.md](CLAUDE.md)
- OpenAI API docs: https://platform.openai.com/docs
- HuggingFace Spaces: https://huggingface.co/docs/hub/spaces

---

**Built with OpenAI GPT-4 and FastAPI** | Deployed on HuggingFace Spaces
