"""
JobFinderAgent - Searches for job postings using OpenAI Agents SDK.
Uses WebSearchTool for real-time job searching without requiring SerpAPI.
"""

from typing import List, Dict, Any
import json
from datetime import datetime
from pathlib import Path

from agents import Agent, WebSearchTool
from pydantic import BaseModel, Field

from config.settings import USER_PROFILE, JOB_POSTINGS_DIR
from models import JobPosting, JobSearchOutput


# Custom tools for the agent

def score_job_match(job: Dict[str, Any]) -> int:
    """
    Calculate match score for a job posting based on user profile.

    Args:
        job: Dictionary containing job details

    Returns:
        Match score from 0-100
    """
    score = 0

    # Role alignment (40 points)
    job_title = job.get('title', '').lower()
    focus_roles = [role.lower() for role in USER_PROFILE.get('focus_roles', [])]
    for role in focus_roles:
        if any(word in job_title for word in role.split()):
            score += 40
            break

    # Location match (20 points)
    job_location = job.get('location', '').lower()
    user_location = USER_PROFILE.get('location', '').lower()
    if user_location in job_location:
        score += 20

    # Language match (20 points)
    description = job.get('description', '').lower()
    requirements = ' '.join(job.get('requirements', [])).lower()
    user_languages = [lang.lower() for lang in USER_PROFILE.get('languages', [])]
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


def save_job_postings(jobs: List[Dict[str, Any]], date: str) -> str:
    """
    Save job postings to JSON file.

    Args:
        jobs: List of job posting dictionaries
        date: Date string (YYYY-MM-DD)

    Returns:
        Path to saved file
    """
    output_file = JOB_POSTINGS_DIR / f"{date}.json"
    JOB_POSTINGS_DIR.mkdir(parents=True, exist_ok=True)

    output_data = {
        "date": date,
        "user_profile": USER_PROFILE,
        "job_count": len(jobs),
        "postings": jobs
    }

    with open(output_file, 'w', encoding='utf-8') as f:
        json.dump(output_data, f, indent=2, ensure_ascii=False)

    print(f"✅ Saved {len(jobs)} job postings to {output_file}")
    return str(output_file)


# Create the JobFinderAgent
def create_job_finder_agent() -> Agent:
    """
    Create and configure the JobFinderAgent using OpenAI Agents SDK.

    Returns:
        Configured Agent instance
    """
    instructions = f"""You are a job search specialist agent. Your role is to search for relevant job postings
using web search and return structured results.

TARGET USER PROFILE:
- Name: {USER_PROFILE.get('name')}
- Location: {USER_PROFILE.get('location')}
- Languages: {', '.join(USER_PROFILE.get('languages', []))}
- Focus Roles: {', '.join(USER_PROFILE.get('focus_roles', []))}

SEARCH CRITERIA:
- Search for: Trainer, Learning & Development (L&D) Specialist, Learning Designer, Experiential Learning Designer, Instructional Designer, Course Designer, Training Designer, Educational Designer, E-Learning Designer positions
- Location: Netherlands (Amsterdam, Rotterdam, The Hague, Utrecht, Eindhoven, Groningen)
- Language: **ENGLISH ONLY** - Do NOT include jobs that require Dutch language skills or are posted in Dutch
- Experience Required: Maximum 5 years (exclude senior/lead roles requiring 5+ years)
- Posting Date: **RECENT ONLY** - Jobs posted within the last 30 days. Exclude expired or old postings
- Sources: LinkedIn, Indeed, Glassdoor, company websites, company career pages
- **GOAL:** Find AT LEAST 8-12 qualified jobs (search broadly if needed)

FOR EACH JOB FOUND, EXTRACT:
1. Job title (exact title from posting - must NOT contain "Senior", "Lead", or "Principal")
2. Company name
3. Location (specific city in Netherlands)
4. Posting date (MUST be within last 30 days - use actual date like "2025-10-15" or "2025-10-23")
5. Job URL (IMPORTANT: Extract the FULL clickable URL, not the shortened display URL.
   If the URL contains '…' or is truncated, try to reconstruct the complete URL from context.
   Example: Instead of 'https://nl.indeed.com/…/job-title', use 'https://nl.indeed.com/viewjob?jk=12345' if available)
6. Brief description (2-3 sentences summarizing the role - MUST be in English)
7. Key requirements (3-5 main qualifications - check that experience required is ≤5 years)
8. Required skills (4-6 technical/soft skills - must NOT include "Dutch language" or "Nederlands")

SEARCH STRATEGY:
1. **Search broadly** - Cast a wide net across multiple sources and cities to find enough candidates
2. Search for variations of each role type (e.g., "Learning Designer", "Instructional Designer", "Training Designer")
3. Search across ALL major Dutch cities: Amsterdam, Rotterdam, The Hague, Utrecht, Eindhoven, Groningen
4. **FILTER OUT** jobs that are:
   - Older than 30 days (check posting date carefully)
   - Require Dutch language proficiency as a requirement
   - Require more than 5 years of experience
   - Senior/Lead/Principal level positions (look for these keywords in title)
5. **INCLUDE ONLY** jobs that:
   - Are posted in English
   - Require 0-5 years of experience (or experience level not specified)
   - Are posted within the last 30 days (be lenient on "Recently" if exact date unknown)
6. Prioritize jobs from known job boards (LinkedIn, Indeed, Glassdoor)
7. Extract structured information from search results
8. **TARGET: Return AT LEAST 8-12 high-quality job postings that meet ALL criteria**
   - Search until you find enough qualified jobs
   - If needed, search additional role variations or locations
   - Quality is important, but quantity matters too - aim for 10+ jobs

OUTPUT FORMAT:
Return a JSON object with this structure:
{{
    "jobs": [
        {{
            "title": "Learning Designer",
            "company": "Company Name",
            "location": "Amsterdam, Netherlands",
            "posting_date": "2025-10-15",
            "url": "https://...",
            "description": "Brief description here",
            "requirements": ["req1", "req2", "req3"],
            "skills": ["skill1", "skill2", "skill3", "skill4"]
        }}
    ],
    "total_found": 8,
    "search_date": "{datetime.now().strftime('%Y-%m-%d')}"
}}

Be thorough but concise. Focus on quality over quantity.

**CRITICAL VALIDATION BEFORE INCLUDING A JOB:**
Before adding a job to your results, verify:
✓ Posting date is within last 30 days (October 2025 or later, or "Recently" for very new jobs)
✓ Job description is in English (not Dutch)
✓ Experience requirement is 0-5 years (or not specified - when in doubt, include it)
✓ Title does NOT contain: "Senior", "Lead", "Principal", "Head of"
✓ Requirements do NOT explicitly require Dutch language proficiency
✓ Job is still active/not expired

If ANY of these checks fail, SKIP that job and continue searching until you have 8-12 qualified jobs.

**IMPORTANT:** Your goal is to find AT LEAST 8-12 jobs. Keep searching different:
- Role variations (e.g., "Instructional Designer", "Course Designer", "Educational Designer")
- Cities (Amsterdam, Rotterdam, Utrecht, The Hague, Eindhoven, Groningen)
- Job boards (LinkedIn, Indeed, Glassdoor, company career pages)
Until you have enough qualified candidates."""

    # Create agent with WebSearchTool
    agent = Agent(
        name="JobFinderAgent",
        instructions=instructions,
        tools=[
            WebSearchTool(
                user_location={
                    "type": "approximate",
                    "city": "Amsterdam"
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
