import os
from dotenv import load_dotenv
from pathlib import Path

load_dotenv()

# API Configuration
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")

# Paths
BASE_DIR = Path(__file__).parent.parent
STORAGE_DIR = BASE_DIR / "storage"
JOB_POSTINGS_DIR = STORAGE_DIR / "job_postings"
APPLICATIONS_DIR = STORAGE_DIR / "applications"
TEMPLATES_DIR = BASE_DIR / "templates"
PROFILES_DIR = BASE_DIR / "profiles"

# Ensure directories exist
JOB_POSTINGS_DIR.mkdir(parents=True, exist_ok=True)
APPLICATIONS_DIR.mkdir(parents=True, exist_ok=True)
TEMPLATES_DIR.mkdir(parents=True, exist_ok=True)
PROFILES_DIR.mkdir(parents=True, exist_ok=True)

# Profile Configuration
ACTIVE_PROFILE_ID = os.getenv("ACTIVE_PROFILE", "name")

# Scheduling
TIMEZONE = os.getenv("TIMEZONE", "Europe/Amsterdam")
SCHEDULE_TIME = os.getenv("SCHEDULE_TIME", "09:00")

# Job URL Scraping Configuration
ENABLE_URL_SCRAPING = os.getenv("ENABLE_URL_SCRAPING", "true").lower() == "true"
MAX_SCRAPING_RETRIES = int(os.getenv("MAX_SCRAPING_RETRIES", "2"))
SCRAPING_TIMEOUT_MS = int(os.getenv("SCRAPING_TIMEOUT_MS", "15000"))

# Legacy User Profile (for backward compatibility)
# This is deprecated - use get_active_user_profile() instead
USER_PROFILE = {
    "name": os.getenv("USER_NAME", "name surname"),
    "location": os.getenv("USER_LOCATION", "Netherlands"),
    "languages": ["English", "Turkish"],
    "focus_roles": ["Trainer", "L&D Specialist", "Learning Designer", "Experiential Learning Designer"],
    "preferred_job_sources": ["LinkedIn", "Glassdoor", "Indeed"]
}


def get_active_user_profile():
    """
    Get the active user profile based on ACTIVE_PROFILE environment variable.

    Returns:
        UserProfile instance

    Raises:
        ImportError: If models are not available (circular import protection)
        FileNotFoundError: If profile doesn't exist
    """
    from config.profile_manager import get_profile_manager

    profile_manager = get_profile_manager(PROFILES_DIR)

    try:
        return profile_manager.load_profile(ACTIVE_PROFILE_ID)
    except FileNotFoundError:
        print(f"⚠️  Profile '{ACTIVE_PROFILE_ID}' not found. Available profiles: {profile_manager.list_profiles()}")
        raise
