# Profile System Architecture

## High-Level Architecture

```
┌─────────────────────────────────────────────────────────────┐
│                     User / Application                      │
└────────────────────────┬────────────────────────────────────┘
                         │
                         ▼
┌─────────────────────────────────────────────────────────────┐
│                  config/settings.py                         │
│  ┌──────────────────────────────────────────────────┐      │
│  │  get_active_user_profile()                       │      │
│  │    - Reads ACTIVE_PROFILE env var                │      │
│  │    - Returns UserProfile object                  │      │
│  └──────────────────┬───────────────────────────────┘      │
└─────────────────────┼───────────────────────────────────────┘
                      │
                      ▼
┌─────────────────────────────────────────────────────────────┐
│              config/profile_manager.py                      │
│  ┌──────────────────────────────────────────────────┐      │
│  │  ProfileManager                                  │      │
│  │    - load_profile(profile_id)                    │      │
│  │    - save_profile(profile)                       │      │
│  │    - list_profiles()                             │      │
│  └──────────────────┬───────────────────────────────┘      │
└─────────────────────┼───────────────────────────────────────┘
                      │
                      ▼
┌─────────────────────────────────────────────────────────────┐
│                    profiles/ directory                      │
│  ┌────────────┐  ┌────────────┐  ┌────────────┐           │
│  │ name.json │  │example.json│  │  your.json │  ...      │
│  └────────────┘  └────────────┘  └────────────┘           │
└─────────────────────┬───────────────────────────────────────┘
                      │
                      ▼
┌─────────────────────────────────────────────────────────────┐
│              models/user_profile.py                         │
│  ┌──────────────────────────────────────────────────┐      │
│  │  UserProfile (Pydantic Model)                    │      │
│  │    ├─ name, email, timezone                      │      │
│  │    └─ search_criteria: SearchCriteria            │      │
│  │         ├─ role_variations                       │      │
│  │         ├─ location_prefs: LocationPreferences   │      │
│  │         ├─ experience: ExperienceRange           │      │
│  │         ├─ languages: [LanguageRequirement]      │      │
│  │         ├─ posting_recency_days                  │      │
│  │         ├─ min/max_target_jobs                   │      │
│  │         └─ job_sources                           │      │
│  └──────────────────┬───────────────────────────────┘      │
└─────────────────────┼───────────────────────────────────────┘
                      │
                      ▼
┌─────────────────────────────────────────────────────────────┐
│           job_agents/job_finder_agent.py                    │
│  ┌──────────────────────────────────────────────────┐      │
│  │  build_job_search_instructions(user_profile)     │      │
│  │    - Generates dynamic instructions from profile │      │
│  │    - Returns formatted instruction string        │      │
│  └──────────────────┬───────────────────────────────┘      │
│  ┌──────────────────┴───────────────────────────────┐      │
│  │  create_job_finder_agent(user_profile=None)      │      │
│  │    - Creates OpenAI Agent with instructions      │      │
│  │    - Configures WebSearchTool                    │      │
│  └──────────────────┬───────────────────────────────┘      │
└─────────────────────┼───────────────────────────────────────┘
                      │
                      ▼
┌─────────────────────────────────────────────────────────────┐
│                    OpenAI Agent                             │
│                  (Job Search Agent)                         │
└─────────────────────────────────────────────────────────────┘
```

## Data Flow

### 1. Profile Loading Flow

```
Application Start
       │
       ▼
Read ACTIVE_PROFILE env var (default: "name")
       │
       ▼
ProfileManager.load_profile(profile_id)
       │
       ▼
Read profiles/{profile_id}.json
       │
       ▼
Validate with Pydantic UserProfile model
       │
       ▼
Return UserProfile object
```

### 2. Agent Creation Flow

```
create_job_finder_agent(profile)
       │
       ▼
get_active_user_profile() [if profile not provided]
       │
       ▼
build_job_search_instructions(profile)
       │
       ├─ Extract role_variations
       ├─ Extract location_prefs
       ├─ Extract experience requirements
       ├─ Extract language requirements
       ├─ Format as agent instructions
       │
       ▼
Create Agent with:
  - Dynamic instructions
  - WebSearchTool configured with user location
  - JobSearchOutput as output_type
       │
       ▼
Return configured Agent
```

### 3. Job Search Flow

```
Agent.run()
       │
       ▼
Use WebSearchTool to search jobs
  - Search in: {cities from profile}
  - Look for: {role_variations from profile}
  - Filter by: {experience, languages, recency from profile}
       │
       ▼
For each job found:
  - Extract job details
  - Validate against criteria
  - Calculate match score (using score_job_match)
       │
       ▼
Return JobSearchOutput
  - jobs: [JobPosting]
  - total_found: int
  - search_date: str
       │
       ▼
save_job_postings(jobs, date, profile)
       │
       ▼
Save to: storage/job_postings/{date}.json
```

## Component Relationships

```
┌────────────────────────────────────────────────────────────┐
│                         Models                             │
├────────────────────────────────────────────────────────────┤
│  User Profile Models     │    Job Models                   │
│  ├─ UserProfile         │    ├─ JobPosting                 │
│  ├─ SearchCriteria      │    ├─ JobSearchOutput            │
│  ├─ LocationPreferences │    ├─ ApplicationMaterials       │
│  ├─ ExperienceRange     │    └─ ApplicationOutput          │
│  └─ LanguageRequirement │                                  │
└──────────┬────────────────────────┬────────────────────────┘
           │                        │
           ▼                        ▼
┌──────────────────────┐  ┌────────────────────────────────┐
│  Profile Manager     │  │    Job Finder Agent            │
├──────────────────────┤  ├────────────────────────────────┤
│  - Load profiles     │  │  - Build instructions          │
│  - Save profiles     │  │  - Create agent                │
│  - List profiles     │  │  - Score matches               │
│  - Validate          │  │  - Save results                │
└──────────┬───────────┘  └────────────┬───────────────────┘
           │                           │
           │         ┌─────────────────┘
           │         │
           ▼         ▼
    ┌──────────────────────┐
    │   Settings           │
    ├──────────────────────┤
    │  - ACTIVE_PROFILE    │
    │  - Paths             │
    │  - get_active_user() │
    └──────────────────────┘
```

## File Dependencies

```
job_finder_agent.py
  ├─ models (JobPosting, JobSearchOutput)
  ├─ models.user_profile (UserProfile)
  ├─ config.settings (get_active_user_profile, JOB_POSTINGS_DIR)
  └─ agents (Agent, WebSearchTool)

profile_manager.py
  └─ models.user_profile (UserProfile)

settings.py
  ├─ config.profile_manager (get_profile_manager)
  └─ pathlib (Path)

user_profile.py
  └─ pydantic (BaseModel, Field)

models/__init__.py
  ├─ models.user_profile (*)
  └─ models.job_models (*)
```

## Environment Variables

```
ACTIVE_PROFILE=name          # Which profile to use (default: name)
OPENAI_API_KEY=sk-...         # OpenAI API key
TIMEZONE=Europe/Amsterdam      # User timezone
SCHEDULE_TIME=09:00           # Scheduled job search time
```

## Storage Structure

```
job_application_flow/
├── profiles/                  # Profile configurations
│   ├── name.json            # Profile: name (L&D, Netherlands)
│   ├── example.json          # Profile: Example (SWE, USA)
│   └── README.md
├── storage/
│   ├── job_postings/         # Search results
│   │   ├── 2025-10-23.json  # Daily job search results
│   │   └── 2025-10-24.json
│   └── applications/         # Generated applications
└── templates/                # Application templates
```

## Key Design Decisions

### 1. Pydantic Models
**Why**: Type safety, validation, IDE autocomplete
**Benefit**: Catch configuration errors early

### 2. JSON Files
**Why**: Human-readable, easy to edit, version-controllable
**Benefit**: Non-developers can modify profiles

### 3. Environment Variables
**Why**: Standard way to configure applications
**Benefit**: Easy switching between profiles

### 4. Singleton Profile Manager
**Why**: Avoid loading profiles multiple times
**Benefit**: Performance optimization

### 5. Dynamic Instructions
**Why**: Single source of truth for search criteria
**Benefit**: Consistency, maintainability

### 6. Backward Compatibility
**Why**: Don't break existing code
**Benefit**: Gradual migration, safety

---

**Legend**:
- `┌─┐ └─┘` = Component/Module
- `│ ▼` = Data flow direction
- `├─` = Contains/Has relationship
- `→` = Depends on/Uses
