# User Profiles

This directory contains user profile configurations for the job search automation system.

## Overview

Each profile is a JSON file that defines:
- Personal information (name, email, timezone)
- Job search criteria (roles, locations, experience level, languages)
- Search parameters (recency, target number of jobs, preferred sources)

## Usage

### Setting the Active Profile

Use the `ACTIVE_PROFILE` environment variable to specify which profile to use:

```bash
export ACTIVE_PROFILE=name
```

Or in your `.env` file:

```
ACTIVE_PROFILE=name
```

If not specified, defaults to `name`.

### Creating a New Profile

1. Copy an existing profile as a template:
   ```bash
   cp profiles/name.json profiles/yourname.json
   ```

2. Edit the JSON file with your information and preferences

3. Set the `ACTIVE_PROFILE` environment variable to use your new profile

### Profile Structure

```json
{
  "name": "Your Name",
  "email": "your.email@example.com",
  "profile_id": "yourname",
  "timezone": "Europe/Amsterdam",
  "search_criteria": {
    "role_variations": [
      "Job Title 1",
      "Job Title 2",
      "Job Title 3"
    ],
    "location_prefs": {
      "country": "Netherlands",
      "cities": ["Amsterdam", "Rotterdam", "Utrecht"],
      "allow_remote": true
    },
    "experience": {
      "min_years": 0,
      "max_years": 5,
      "exclude_senior_roles": true
    },
    "languages": [
      {
        "language": "English",
        "required": true,
        "exclude_if_required": false
      },
      {
        "language": "Dutch",
        "required": false,
        "exclude_if_required": true
      }
    ],
    "posting_recency_days": 30,
    "min_target_jobs": 8,
    "max_target_jobs": 12,
    "job_sources": ["LinkedIn", "Indeed", "Glassdoor"]
  }
}
```

### Configuration Options

#### Basic Information
- `name`: Your full name
- `email`: Your email address (optional)
- `profile_id`: Unique identifier (should match filename without .json)
- `timezone`: Your timezone (e.g., "Europe/Amsterdam", "America/New_York")

#### Search Criteria

**role_variations**: List of job titles to search for
- Include variations and synonyms
- Examples: "L&D Specialist", "Learning Designer", "Instructional Designer"

**location_prefs**:
- `country`: Target country for job search
- `cities`: List of preferred cities
- `allow_remote`: Whether to include remote positions

**experience**:
- `min_years`: Minimum years of experience
- `max_years`: Maximum years of experience
- `exclude_senior_roles`: Filter out Senior/Lead/Principal positions

**languages**: List of language requirements
- `language`: Language name
- `required`: Whether this language is required for you
- `exclude_if_required`: Exclude jobs requiring this language (e.g., Dutch if you don't speak it)

**posting_recency_days**: Only search for jobs posted within this many days (e.g., 30 for last month)

**min_target_jobs** / **max_target_jobs**: Target range for number of jobs to find

**job_sources**: Preferred job boards to search (e.g., "LinkedIn", "Indeed", "Glassdoor")

## Managing Profiles Programmatically

```python
from config.profile_manager import ProfileManager
from pathlib import Path

# Initialize profile manager
pm = ProfileManager(Path('profiles'))

# List all profiles
profiles = pm.list_profiles()
print(profiles)  # ['name', 'example']

# Load a profile
profile = pm.load_profile('name')
print(profile.name)  # 'name surname'

# Check if profile exists
exists = pm.profile_exists('name')  # True

# Save a modified profile
pm.save_profile(profile, 'name')
```

## Examples

See `name.json` for a Learning & Development specialist profile targeting Netherlands.

See `example.json` for a Software Engineer profile targeting United States.
