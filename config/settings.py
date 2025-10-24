import os
from dotenv import load_dotenv
from pathlib import Path

load_dotenv()

# API Configuration
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")

# User Profile
USER_PROFILE = {
    "name": os.getenv("USER_NAME", "Seray Soyman"),
    "location": os.getenv("USER_LOCATION", "Netherlands"),
    "languages": ["English", "Turkish"],
    "focus_roles": ["Trainer", "L&D Specialist", "Learning Designer", "Experiential Learning Designer"],
    "preferred_job_sources": ["LinkedIn", "Glassdoor", "Indeed"]
}

# Scheduling
TIMEZONE = os.getenv("TIMEZONE", "Europe/Amsterdam")
SCHEDULE_TIME = os.getenv("SCHEDULE_TIME", "09:00")

# Paths
BASE_DIR = Path(__file__).parent.parent
STORAGE_DIR = BASE_DIR / "storage"
JOB_POSTINGS_DIR = STORAGE_DIR / "job_postings"
APPLICATIONS_DIR = STORAGE_DIR / "applications"
TEMPLATES_DIR = BASE_DIR / "templates"

# Ensure directories exist
JOB_POSTINGS_DIR.mkdir(parents=True, exist_ok=True)
APPLICATIONS_DIR.mkdir(parents=True, exist_ok=True)
TEMPLATES_DIR.mkdir(parents=True, exist_ok=True)
