"""
JobFinderAgent - Searches for job postings using OpenAI Agents SDK.
Uses WebSearchTool for real-time job searching without requiring SerpAPI.
"""

from typing import List, Dict, Any, Optional
import json
from datetime import datetime
from pathlib import Path

from agents import Agent, WebSearchTool
from pydantic import BaseModel, Field

from config.settings import JOB_POSTINGS_DIR, get_active_user_profile
from models.user_profile import UserProfile
from models import JobPosting, JobSearchOutput


# Custom tools for the agent

def score_job_match(job: Dict[str, Any], user_profile: UserProfile) -> int:
    """
    Calculate match score for a job posting based on user profile.

    Args:
        job: Dictionary containing job details
        user_profile: UserProfile instance

    Returns:
        Match score from 0-100
    """
    score = 0

    # Role alignment (40 points)
    job_title = job.get('title', '').lower()
    focus_roles = [role.lower() for role in user_profile.search_criteria.role_variations]
    for role in focus_roles:
        if any(word in job_title for word in role.split()):
            score += 40
            break

    # Location match (20 points)
    job_location = job.get('location', '').lower()
    user_location = user_profile.search_criteria.location_prefs.country.lower()
    if user_location in job_location:
        score += 20

    # Language match (20 points)
    description = job.get('description', '').lower()
    requirements = ' '.join(job.get('requirements', [])).lower()
    user_languages = [
        lang.language.lower()
        for lang in user_profile.search_criteria.languages
        if lang.required
    ]
    for lang in user_languages:
        if lang in description or lang in requirements:
            score += 20
            break

    # Skills presence (20 points)
    skills = job.get('skills', [])
    if len(skills) >= 3:
        score += 20
    elif len(skills) >= 1:
        score += 10

    return min(100, max(0, score))


def save_job_postings(jobs: List[Dict[str, Any]], date: str, user_profile: UserProfile) -> str:
    """
    Save job postings to JSON file.

    Args:
        jobs: List of job posting dictionaries
        date: Date string (YYYY-MM-DD)
        user_profile: UserProfile instance

    Returns:
        Path to saved file
    """
    output_file = JOB_POSTINGS_DIR / f"{date}.json"
    JOB_POSTINGS_DIR.mkdir(parents=True, exist_ok=True)

    # Convert user profile to legacy format for backward compatibility
    legacy_profile = {
        "name": user_profile.name,
        "location": user_profile.search_criteria.location_prefs.country,
        "languages": [lang.language for lang in user_profile.search_criteria.languages if lang.required],
        "focus_roles": user_profile.search_criteria.role_variations[:4],  # Take first 4 for compatibility
        "preferred_job_sources": user_profile.search_criteria.job_sources
    }

    output_data = {
        "date": date,
        "user_profile": legacy_profile,
        "job_count": len(jobs),
        "postings": jobs
    }

    with open(output_file, 'w', encoding='utf-8') as f:
        json.dump(output_data, f, indent=2, ensure_ascii=False)

    print(f"✅ Saved {len(jobs)} job postings to {output_file}")
    return str(output_file)


def build_job_search_instructions(user_profile: UserProfile) -> str:
    """
    Build dynamic job search instructions based on user profile.

    Args:
        user_profile: UserProfile instance

    Returns:
        Formatted instruction string for the agent
    """
    criteria = user_profile.search_criteria

    # Build language requirements
    required_languages = [lang.language for lang in criteria.languages if lang.required]
    excluded_languages = [lang.language for lang in criteria.languages if lang.exclude_if_required]

    language_instruction = ""
    if required_languages:
        language_instruction = f"**{required_languages[0].upper()} ONLY**"
        if excluded_languages:
            excluded_str = ', '.join(excluded_languages)
            language_instruction += f" - Do NOT include jobs that require {excluded_str} language skills or are posted in {excluded_str}"

    # Build seniority filter
    seniority_keywords = '"Senior", "Lead", "Principal", "Head of"' if criteria.experience.exclude_senior_roles else ''
    seniority_note = f"must NOT contain {seniority_keywords}" if seniority_keywords else "any seniority level"

    # Build location string
    cities_str = ', '.join(criteria.location_prefs.cities)

    # Build role variations string
    roles_str = ', '.join(criteria.role_variations)

    # Build excluded language requirements for filtering
    excluded_lang_filter = ""
    if excluded_languages:
        excluded_lang_filter = f"must NOT include \"{', '.join(excluded_languages)} language\" or \"{', '.join([l.lower() + 's' for l in excluded_languages])}\""

    instructions = f"""You are a job search specialist agent. Your role is to search for relevant job postings
using web search and return structured results.

TARGET USER PROFILE:
- Name: {user_profile.name}
- Location: {criteria.location_prefs.country}
- Required Languages: {', '.join(required_languages)}
- Focus Roles: {roles_str}

SEARCH CRITERIA:
- Search for: {roles_str} positions
- Location: {criteria.location_prefs.country} ({cities_str})
- Language: {language_instruction}
- Experience Required: {criteria.experience.min_years}-{criteria.experience.max_years} years{' (exclude senior/lead roles requiring ' + str(criteria.experience.max_years) + '+ years)' if criteria.experience.exclude_senior_roles else ''}
- Posting Date: **RECENT ONLY** - Jobs posted within the last {criteria.posting_recency_days} days. Exclude expired or old postings
- Sources: {', '.join(criteria.job_sources)}
- **GOAL:** Find AT LEAST {criteria.min_target_jobs}-{criteria.max_target_jobs} qualified jobs (search broadly if needed)

FOR EACH JOB FOUND, EXTRACT:
1. Job title (exact title from posting - {seniority_note})
2. Company name
3. Location (specific city in {criteria.location_prefs.country})
4. Posting date (MUST be within last {criteria.posting_recency_days} days - use actual date like "2025-10-15" or "2025-10-23")
5. Job URL (IMPORTANT: Extract the FULL clickable URL, not the shortened display URL.
   If the URL contains '…' or is truncated, try to reconstruct the complete URL from context.
   Example: Instead of 'https://nl.indeed.com/…/job-title', use 'https://nl.indeed.com/viewjob?jk=12345' if available)
6. Brief description (2-3 sentences summarizing the role - MUST be in {required_languages[0] if required_languages else 'English'})
7. Key requirements (3-5 main qualifications - check that experience required is ≤{criteria.experience.max_years} years)
8. Required skills (4-6 technical/soft skills{' - ' + excluded_lang_filter if excluded_lang_filter else ''})

SEARCH STRATEGY:
1. **Search broadly** - Cast a wide net across multiple sources and cities to find enough candidates
2. Search for variations of each role type (e.g., {', '.join([f'"{r}"' for r in criteria.role_variations[:3]])})
3. Search across ALL major cities: {cities_str}
4. **FILTER OUT** jobs that are:
   - Older than {criteria.posting_recency_days} days (check posting date carefully)
   {'- Require ' + ', '.join(excluded_languages) + ' language proficiency as a requirement' if excluded_languages else ''}
   - Require more than {criteria.experience.max_years} years of experience
   {f'- {seniority_keywords} level positions (look for these keywords in title)' if seniority_keywords else ''}
5. **INCLUDE ONLY** jobs that:
   - Are posted in {required_languages[0] if required_languages else 'English'}
   - Require {criteria.experience.min_years}-{criteria.experience.max_years} years of experience (or experience level not specified)
   - Are posted within the last {criteria.posting_recency_days} days (be lenient on "Recently" if exact date unknown)
6. Prioritize jobs from known job boards ({', '.join(criteria.job_sources[:3])})
7. Extract structured information from search results
8. **TARGET: Return AT LEAST {criteria.min_target_jobs}-{criteria.max_target_jobs} high-quality job postings that meet ALL criteria**
   - Search until you find enough qualified jobs
   - If needed, search additional role variations or locations
   - Quality is important, but quantity matters too - aim for {criteria.min_target_jobs}+ jobs

OUTPUT FORMAT:
Return a JSON object with this structure:
{{{{
    "jobs": [
        {{{{
            "title": "Learning Designer",
            "company": "Company Name",
            "location": "{cities_str.split(',')[0].strip()}, {criteria.location_prefs.country}",
            "posting_date": "2025-10-15",
            "url": "https://...",
            "description": "Brief description here",
            "requirements": ["req1", "req2", "req3"],
            "skills": ["skill1", "skill2", "skill3", "skill4"]
        }}}}
    ],
    "total_found": {criteria.min_target_jobs},
    "search_date": "{datetime.now().strftime('%Y-%m-%d')}"
}}}}

Be thorough but concise. Focus on quality over quantity.

**CRITICAL VALIDATION BEFORE INCLUDING A JOB:**
Before adding a job to your results, verify:
✓ Posting date is within last {criteria.posting_recency_days} days (October 2025 or later, or "Recently" for very new jobs)
✓ Job description is in {required_languages[0] if required_languages else 'English'} (not {excluded_languages[0] if excluded_languages else 'other languages'})
✓ Experience requirement is {criteria.experience.min_years}-{criteria.experience.max_years} years (or not specified - when in doubt, include it)
{f'✓ Title does NOT contain: {seniority_keywords}' if seniority_keywords else ''}
{f'✓ Requirements do NOT explicitly require {", ".join(excluded_languages)} language proficiency' if excluded_languages else ''}
✓ Job is still active/not expired

If ANY of these checks fail, SKIP that job and continue searching until you have {criteria.min_target_jobs}-{criteria.max_target_jobs} qualified jobs.

**IMPORTANT:** Your goal is to find AT LEAST {criteria.min_target_jobs}-{criteria.max_target_jobs} jobs. Keep searching different:
- Role variations (e.g., {', '.join([f'"{r}"' for r in criteria.role_variations[:3]])})
- Cities ({cities_str})
- Job boards ({', '.join(criteria.job_sources)})
Until you have enough qualified candidates."""

    return instructions


# Create the JobFinderAgent
def create_job_finder_agent(user_profile: Optional[UserProfile] = None) -> Agent:
    """
    Create and configure the JobFinderAgent using OpenAI Agents SDK.

    Args:
        user_profile: Optional UserProfile. If not provided, loads from settings.

    Returns:
        Configured Agent instance
    """
    if user_profile is None:
        user_profile = get_active_user_profile()

    instructions = build_job_search_instructions(user_profile)

    # Use first city or default to country capital for location context
    default_city = (
        user_profile.search_criteria.location_prefs.cities[0]
        if user_profile.search_criteria.location_prefs.cities
        else "Amsterdam"
    )

    # Create agent with WebSearchTool
    agent = Agent(
        name="JobFinderAgent",
        instructions=instructions,
        tools=[
            WebSearchTool(
                user_location={
                    "type": "approximate",
                    "city": default_city
                }
            )
        ],
        output_type=JobSearchOutput
    )

    return agent


def get_latest_job_postings() -> List[Dict[str, Any]]:
    """
    Retrieve the most recent job postings from storage.

    Returns:
        List of job posting dictionaries
    """
    json_files = sorted(JOB_POSTINGS_DIR.glob("*.json"), reverse=True)

    if not json_files:
        return []

    latest_file = json_files[0]
    with open(latest_file, 'r', encoding='utf-8') as f:
        data = json.load(f)
        return data.get("postings", [])


# Export the agent creator function
__all__ = ['create_job_finder_agent', 'score_job_match', 'save_job_postings', 'get_latest_job_postings']
