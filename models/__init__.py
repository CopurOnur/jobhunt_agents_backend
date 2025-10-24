"""
Models package for the job application flow.
"""

# User profile models
from .user_profile import (
    UserProfile,
    SearchCriteria,
    LocationPreferences,
    ExperienceRange,
    LanguageRequirement
)

# Job models
from .job_models import (
    JobPosting,
    JobSearchOutput,
    ApplicationMaterials,
    ApplicationOutput,
    UserProvidedMaterials
)

__all__ = [
    # User profile models
    'UserProfile',
    'SearchCriteria',
    'LocationPreferences',
    'ExperienceRange',
    'LanguageRequirement',
    # Job models
    'JobPosting',
    'JobSearchOutput',
    'ApplicationMaterials',
    'ApplicationOutput',
    'UserProvidedMaterials'
]
