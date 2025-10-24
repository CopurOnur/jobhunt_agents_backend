"""
Configuration package for job application workflow.
"""

from config.settings import (
    OPENAI_API_KEY,
    USER_PROFILE,
    TIMEZONE,
    SCHEDULE_TIME,
    BASE_DIR,
    STORAGE_DIR,
    JOB_POSTINGS_DIR,
    APPLICATIONS_DIR,
    TEMPLATES_DIR
)

__all__ = [
    'OPENAI_API_KEY',
    'USER_PROFILE',
    'TIMEZONE',
    'SCHEDULE_TIME',
    'BASE_DIR',
    'STORAGE_DIR',
    'JOB_POSTINGS_DIR',
    'APPLICATIONS_DIR',
    'TEMPLATES_DIR'
]
