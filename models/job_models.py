"""
Pydantic models for structured outputs in the job application flow.
"""

from typing import List, Optional
from pydantic import BaseModel, Field


class JobPosting(BaseModel):
    """Structured model for a single job posting."""
    title: str = Field(description="Job title")
    company: str = Field(description="Company name")
    location: str = Field(description="Job location (city, country)")
    posting_date: Optional[str] = Field(default="Recently", description="When the job was posted")
    url: str = Field(description="URL to the job posting")
    description: str = Field(description="Brief job description (2-3 sentences)")
    requirements: List[str] = Field(default_factory=list, description="Key job requirements")
    skills: List[str] = Field(default_factory=list, description="Required skills")
    match_score: int = Field(default=0, ge=0, le=100, description="Match score (0-100)")


class JobSearchOutput(BaseModel):
    """Output model for job search results."""
    jobs: List[JobPosting] = Field(description="List of job postings found")
    total_found: int = Field(description="Total number of jobs found")
    search_date: str = Field(description="Date when search was performed")


class ApplicationMaterials(BaseModel):
    """Output model for generated application materials."""
    company: str = Field(description="Company name")
    position: str = Field(description="Job position/title")
    customized_cv: str = Field(description="Customized CV content in markdown")
    motivation_letter: str = Field(description="Motivation letter content in markdown")
    match_summary: str = Field(description="Match analysis summary in markdown")


class ApplicationOutput(BaseModel):
    """Output model for application generation result."""
    materials: ApplicationMaterials
    cv_path: str = Field(description="Path to saved CV file")
    letter_path: str = Field(description="Path to saved motivation letter file")
    summary_path: str = Field(description="Path to saved match summary file")
    output_directory: str = Field(description="Directory containing all files")
