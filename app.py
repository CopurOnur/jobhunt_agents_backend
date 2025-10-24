"""
FastAPI application for Job Application Flow.
Provides REST API endpoints to trigger the multi-agent job search workflow.
"""

from fastapi import FastAPI, BackgroundTasks, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import Dict, Any, Optional, List
import uuid
from datetime import datetime
import os

from workflow import JobApplicationWorkflow

app = FastAPI(
    title="Job Application Flow API",
    description="Multi-agent system for automated job search and application generation",
    version="1.0.0"
)

# CORS middleware for frontend access
# Determine allowed origins based on environment
ALLOWED_ORIGINS = [
    "http://localhost:3000",  # Local development
    "http://localhost:3001",
]

# Add HuggingFace Spaces domain if running on HF
if os.getenv("SPACE_ID"):  # HuggingFace Spaces sets this env var
    hf_space_host = os.getenv("SPACE_HOST", "")
    if hf_space_host:
        ALLOWED_ORIGINS.append(f"https://{hf_space_host}")
    # Also allow the HuggingFace iframe
    ALLOWED_ORIGINS.append("https://huggingface.co")

# For local development, allow all origins
if not os.getenv("SPACE_ID"):
    ALLOWED_ORIGINS.append("*")

app.add_middleware(
    CORSMiddleware,
    allow_origins=ALLOWED_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
    expose_headers=["*"],  # Allow frontend to read response headers
)

# In-memory storage for job execution status
# In production, use Redis or a database
job_status_store: Dict[str, Dict[str, Any]] = {}

# Models
class TriggerResponse(BaseModel):
    job_id: str
    status: str
    message: str
    timestamp: str

class StatusResponse(BaseModel):
    job_id: str
    status: str
    jobs_found: Optional[int] = None
    applications_generated: Optional[int] = None
    error: Optional[str] = None
    started_at: Optional[str] = None
    completed_at: Optional[str] = None

class ResultsResponse(BaseModel):
    job_id: str
    status: str
    job_postings: list
    applications: list
    summary: Optional[str] = None

class JobSearchResponse(BaseModel):
    search_id: str
    status: str
    message: str
    timestamp: str

class JobPostingsResponse(BaseModel):
    search_id: str
    status: str
    job_postings: list

class GenerateApplicationsRequest(BaseModel):
    job_ids: List[str]  # List of selected job posting IDs/indices

class GenerateApplicationsResponse(BaseModel):
    generation_id: str
    status: str
    message: str
    selected_jobs_count: int
    timestamp: str


async def run_workflow_task(job_id: str):
    """
    Background task to run the job application workflow.
    Updates job_status_store with progress and results.
    """
    try:
        # Update status to running
        job_status_store[job_id]["status"] = "running"
        job_status_store[job_id]["started_at"] = datetime.now().isoformat()

        # Execute workflow
        workflow = JobApplicationWorkflow(session_id=job_id)
        result = await workflow.run_once_for_api()

        # Update with results
        job_status_store[job_id].update({
            "status": "completed",
            "completed_at": datetime.now().isoformat(),
            "jobs_found": result.get("job_count", 0),
            "applications_generated": result.get("applications_generated", 0),
            "results": result
        })

    except Exception as e:
        import traceback
        error_details = traceback.format_exc()
        print(f"❌ Workflow failed: {error_details}")
        # Update with error
        job_status_store[job_id].update({
            "status": "failed",
            "completed_at": datetime.now().isoformat(),
            "error": str(e),
            "error_details": error_details
        })


@app.get("/")
def root():
    """Root endpoint with API information."""
    return {
        "name": "Job Application Flow API",
        "version": "1.0.0",
        "endpoints": {
            "/api/trigger": "POST - Trigger job search workflow",
            "/api/status/{job_id}": "GET - Check workflow execution status",
            "/api/results/{job_id}": "GET - Get workflow results",
            "/health": "GET - Health check"
        }
    }


@app.get("/health")
def health_check():
    """Health check endpoint for monitoring."""
    return {
        "status": "healthy",
        "timestamp": datetime.now().isoformat(),
        "service": "job-application-flow"
    }


@app.post("/api/trigger", response_model=TriggerResponse)
async def trigger_workflow(background_tasks: BackgroundTasks):
    """
    Trigger the job search and application generation workflow.

    This endpoint starts the workflow as a background task and returns immediately.
    Use the /api/status/{job_id} endpoint to check progress.

    Returns:
        job_id: Unique identifier for this workflow execution
        status: Current status (pending)
        message: Informational message
        timestamp: When the request was received
    """
    # Generate unique job ID
    job_id = str(uuid.uuid4())

    # Initialize job status
    job_status_store[job_id] = {
        "job_id": job_id,
        "status": "pending",
        "created_at": datetime.now().isoformat(),
        "started_at": None,
        "completed_at": None
    }

    # Add background task
    background_tasks.add_task(run_workflow_task, job_id)

    return TriggerResponse(
        job_id=job_id,
        status="pending",
        message="Workflow has been queued and will start shortly",
        timestamp=datetime.now().isoformat()
    )


@app.get("/api/status/{job_id}", response_model=StatusResponse)
def get_workflow_status(job_id: str):
    """
    Check the status of a workflow execution.

    Args:
        job_id: The unique identifier returned by /api/trigger

    Returns:
        StatusResponse with current execution status and results (if completed)

    Raises:
        404: If job_id is not found
    """
    if job_id not in job_status_store:
        raise HTTPException(status_code=404, detail=f"Job ID '{job_id}' not found")

    job_info = job_status_store[job_id]

    return StatusResponse(
        job_id=job_id,
        status=job_info["status"],
        jobs_found=job_info.get("jobs_found"),
        applications_generated=job_info.get("applications_generated"),
        error=job_info.get("error"),
        started_at=job_info.get("started_at"),
        completed_at=job_info.get("completed_at")
    )


@app.get("/api/results/{job_id}", response_model=ResultsResponse)
def get_workflow_results(job_id: str):
    """
    Get the detailed results of a completed workflow execution.

    Args:
        job_id: The unique identifier returned by /api/trigger

    Returns:
        ResultsResponse with job postings, applications, and summary

    Raises:
        404: If job_id is not found
        400: If workflow is not yet completed
    """
    if job_id not in job_status_store:
        raise HTTPException(status_code=404, detail=f"Job ID '{job_id}' not found")

    job_info = job_status_store[job_id]

    if job_info["status"] not in ["completed", "failed"]:
        raise HTTPException(
            status_code=400,
            detail=f"Workflow is still {job_info['status']}. Please wait for completion."
        )

    if job_info["status"] == "failed":
        raise HTTPException(
            status_code=500,
            detail=f"Workflow failed: {job_info.get('error', 'Unknown error')}"
        )

    results = job_info.get("results", {})

    return ResultsResponse(
        job_id=job_id,
        status=job_info["status"],
        job_postings=results.get("job_postings", []),
        applications=results.get("applications", []),
        summary=results.get("summary")
    )


@app.delete("/api/cleanup/{job_id}")
def cleanup_job(job_id: str):
    """
    Delete a job from the status store.
    Useful for cleaning up old completed jobs.

    Args:
        job_id: The unique identifier to delete

    Returns:
        Success message

    Raises:
        404: If job_id is not found
    """
    if job_id not in job_status_store:
        raise HTTPException(status_code=404, detail=f"Job ID '{job_id}' not found")

    del job_status_store[job_id]

    return {
        "message": f"Job {job_id} has been deleted",
        "timestamp": datetime.now().isoformat()
    }


@app.get("/api/jobs")
def list_all_jobs():
    """
    List all jobs in the system with their current status.
    Useful for monitoring and debugging.

    Returns:
        List of all jobs with their status
    """
    jobs = []
    for job_id, job_info in job_status_store.items():
        jobs.append({
            "job_id": job_id,
            "status": job_info["status"],
            "created_at": job_info.get("created_at"),
            "completed_at": job_info.get("completed_at"),
            "jobs_found": job_info.get("jobs_found"),
            "applications_generated": job_info.get("applications_generated")
        })

    return {
        "total_jobs": len(jobs),
        "jobs": jobs
    }


# NEW ENDPOINTS FOR FRONTEND

async def run_job_search_task(search_id: str):
    """
    Background task to run ONLY the job search (no application generation).
    Updates job_status_store with job postings and match scores.
    """
    try:
        job_status_store[search_id]["status"] = "running"
        job_status_store[search_id]["started_at"] = datetime.now().isoformat()

        # Execute only job search
        workflow = JobApplicationWorkflow(session_id=search_id)
        result = await workflow.run_job_search_only()

        # Update with results
        job_status_store[search_id].update({
            "status": "completed",
            "completed_at": datetime.now().isoformat(),
            "jobs_found": result.get("job_count", 0),
            "results": result
        })

    except Exception as e:
        import traceback
        error_details = traceback.format_exc()
        print(f"❌ Job search failed: {error_details}")
        job_status_store[search_id].update({
            "status": "failed",
            "completed_at": datetime.now().isoformat(),
            "error": str(e),
            "error_details": error_details
        })


async def run_application_generation_task(generation_id: str, selected_job_ids: List[str]):
    """
    Background task to generate applications for selected job IDs only.
    """
    try:
        job_status_store[generation_id]["status"] = "running"
        job_status_store[generation_id]["started_at"] = datetime.now().isoformat()

        # Get the search results to find the selected jobs
        search_id = job_status_store[generation_id].get("search_id")
        if not search_id or search_id not in job_status_store:
            raise ValueError("Search ID not found or invalid")

        search_results = job_status_store[search_id].get("results", {})
        all_job_postings = search_results.get("job_postings", [])

        # Filter selected jobs
        selected_jobs = [job for i, job in enumerate(all_job_postings) if str(i) in selected_job_ids]

        # Execute application generation
        workflow = JobApplicationWorkflow(session_id=generation_id)
        result = await workflow.run_application_generation(selected_jobs)

        # Update with results
        job_status_store[generation_id].update({
            "status": "completed",
            "completed_at": datetime.now().isoformat(),
            "applications_generated": result.get("applications_generated", 0),
            "results": result
        })

    except Exception as e:
        import traceback
        error_details = traceback.format_exc()
        print(f"❌ Application generation failed: {error_details}")
        job_status_store[generation_id].update({
            "status": "failed",
            "completed_at": datetime.now().isoformat(),
            "error": str(e),
            "error_details": error_details
        })


@app.post("/api/search-jobs", response_model=JobSearchResponse)
async def search_jobs(background_tasks: BackgroundTasks):
    """
    Trigger ONLY job search (no application generation).
    Frontend endpoint to search for jobs and get match scores.

    Returns:
        search_id: Unique identifier for this search
        status: Current status (pending)
    """
    search_id = str(uuid.uuid4())

    job_status_store[search_id] = {
        "search_id": search_id,
        "type": "job_search",
        "status": "pending",
        "created_at": datetime.now().isoformat(),
        "started_at": None,
        "completed_at": None
    }

    background_tasks.add_task(run_job_search_task, search_id)

    return JobSearchResponse(
        search_id=search_id,
        status="pending",
        message="Job search has been queued and will start shortly",
        timestamp=datetime.now().isoformat()
    )


@app.get("/api/search-jobs/{search_id}", response_model=JobPostingsResponse)
def get_job_postings(search_id: str):
    """
    Get job postings from a completed job search.

    Args:
        search_id: The unique identifier returned by /api/search-jobs

    Returns:
        JobPostingsResponse with list of job postings (sorted by match score)
    """
    if search_id not in job_status_store:
        raise HTTPException(status_code=404, detail=f"Search ID '{search_id}' not found")

    search_info = job_status_store[search_id]

    if search_info["status"] == "pending" or search_info["status"] == "running":
        return JobPostingsResponse(
            search_id=search_id,
            status=search_info["status"],
            job_postings=[]
        )

    if search_info["status"] == "failed":
        raise HTTPException(
            status_code=500,
            detail=f"Job search failed: {search_info.get('error', 'Unknown error')}"
        )

    results = search_info.get("results", {})
    job_postings = results.get("job_postings", [])

    # Sort by match_score if available (highest first)
    sorted_postings = sorted(
        job_postings,
        key=lambda x: x.get("match_score", 0),
        reverse=True
    )

    return JobPostingsResponse(
        search_id=search_id,
        status=search_info["status"],
        job_postings=sorted_postings
    )


@app.post("/api/generate-applications", response_model=GenerateApplicationsResponse)
async def generate_applications(
    request: GenerateApplicationsRequest,
    background_tasks: BackgroundTasks,
    search_id: str = None
):
    """
    Generate applications for selected job postings only.

    Args:
        request: Contains job_ids (list of indices as strings)
        search_id: Optional search_id to link to previous search

    Returns:
        generation_id: Unique identifier for this generation task
    """
    generation_id = str(uuid.uuid4())

    job_status_store[generation_id] = {
        "generation_id": generation_id,
        "type": "application_generation",
        "status": "pending",
        "search_id": search_id,
        "selected_job_ids": request.job_ids,
        "created_at": datetime.now().isoformat(),
        "started_at": None,
        "completed_at": None
    }

    background_tasks.add_task(
        run_application_generation_task,
        generation_id,
        request.job_ids
    )

    return GenerateApplicationsResponse(
        generation_id=generation_id,
        status="pending",
        message="Application generation has been queued",
        selected_jobs_count=len(request.job_ids),
        timestamp=datetime.now().isoformat()
    )


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=7860)
