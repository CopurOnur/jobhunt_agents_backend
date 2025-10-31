"""
User Profile model for configurable job search criteria.
"""

from typing import List, Optional
from pydantic import BaseModel, Field


class LocationPreferences(BaseModel):
    """Location preferences for job search."""
    country: str = Field(description="Target country for job search")
    cities: List[str] = Field(description="List of preferred cities")
    allow_remote: bool = Field(default=True, description="Include remote positions")


class ExperienceRange(BaseModel):
    """Experience level requirements."""
    min_years: int = Field(default=0, ge=0, description="Minimum years of experience")
    max_years: int = Field(default=5, ge=0, description="Maximum years of experience")
    exclude_senior_roles: bool = Field(default=True, description="Exclude senior/lead/principal positions")


class LanguageRequirement(BaseModel):
    """Language requirement specification."""
    language: str = Field(description="Language name (e.g., 'English', 'Dutch')")
    required: bool = Field(default=True, description="Whether this language is required")
    exclude_if_required: bool = Field(default=False, description="Exclude jobs that require this language")


class SearchCriteria(BaseModel):
    """Job search criteria configuration."""
    role_variations: List[str] = Field(
        description="List of job role variations to search for"
    )
    location_prefs: LocationPreferences = Field(description="Location preferences")
    experience: ExperienceRange = Field(description="Experience level requirements")
    languages: List[LanguageRequirement] = Field(description="Language requirements")
    posting_recency_days: int = Field(
        default=30,
        ge=1,
        description="Only include jobs posted within this many days"
    )
    min_target_jobs: int = Field(
        default=8,
        ge=1,
        description="Minimum number of jobs to find"
    )
    max_target_jobs: int = Field(
        default=12,
        ge=1,
        description="Maximum number of jobs to target"
    )
    job_sources: List[str] = Field(
        default_factory=lambda: ["LinkedIn", "Indeed", "Glassdoor"],
        description="Preferred job sources/boards"
    )


class UserProfile(BaseModel):
    """Complete user profile for job search automation."""

    # Basic Information
    name: str = Field(description="User's full name")
    email: Optional[str] = Field(default=None, description="User's email address")

    # Search Criteria
    search_criteria: SearchCriteria = Field(description="Job search criteria")

    # Additional metadata
    profile_id: Optional[str] = Field(default=None, description="Unique profile identifier")
    timezone: str = Field(default="Europe/Amsterdam", description="User's timezone")

    class Config:
        json_schema_extra = {
            "example": {
                "name": "name surname",
                "email": "seray@example.com",
                "profile_id": "seray",
                "timezone": "Europe/Amsterdam",
                "search_criteria": {
                    "role_variations": [
                        "Trainer",
                        "Learning & Development Specialist",
                        "Learning Designer",
                        "Experiential Learning Designer",
                        "Instructional Designer",
                        "Course Designer"
                    ],
                    "location_prefs": {
                        "country": "Netherlands",
                        "cities": ["Amsterdam", "Rotterdam", "The Hague", "Utrecht"],
                        "allow_remote": True
                    },
                    "experience": {
                        "min_years": 0,
                        "max_years": 5,
                        "exclude_senior_roles": True
                    },
                    "languages": [
                        {"language": "English", "required": True, "exclude_if_required": False},
                        {"language": "Dutch", "required": False, "exclude_if_required": True}
                    ],
                    "posting_recency_days": 30,
                    "min_target_jobs": 8,
                    "max_target_jobs": 12,
                    "job_sources": ["LinkedIn", "Indeed", "Glassdoor"]
                }
            }
        }
