# Migration Guide: Configurable User Profiles

This guide explains the changes made to support multiple configurable user profiles.

## What Changed?

### Before (Hardcoded Configuration)
- Job search criteria were hardcoded in `job_finder_agent.py`
- User profile was a simple dictionary in `config/settings.py`
- No easy way to switch between different job search configurations

### After (Configurable Profiles)
- Job search criteria are now loaded from JSON profile files in `profiles/` directory
- User profiles are validated Pydantic models with full type safety
- Easy switching between profiles using `ACTIVE_PROFILE` environment variable
- All search parameters are configurable per profile

## New Structure

```
job_application_flow/
├── profiles/                    # New: Profile configurations
│   ├── seray.json              # Existing user profile
│   ├── example.json            # Example profile
│   └── README.md               # Documentation
├── models/                      # Reorganized
│   ├── __init__.py             # Re-exports all models
│   ├── user_profile.py         # New: Profile models
│   └── job_models.py           # Moved from models.py
├── config/
│   ├── settings.py             # Updated: Profile loading
│   └── profile_manager.py      # New: Profile management
└── job_agents/
    └── job_finder_agent.py     # Updated: Dynamic instructions
```

## Breaking Changes

### 1. Function Signatures

**`score_job_match(job)` → `score_job_match(job, user_profile)`**
```python
# Before
score = score_job_match(job_dict)

# After
from config.settings import get_active_user_profile
profile = get_active_user_profile()
score = score_job_match(job_dict, profile)
```

**`save_job_postings(jobs, date)` → `save_job_postings(jobs, date, user_profile)`**
```python
# Before
save_job_postings(jobs, "2025-10-23")

# After
from config.settings import get_active_user_profile
profile = get_active_user_profile()
save_job_postings(jobs, "2025-10-23", profile)
```

**`create_job_finder_agent()` → `create_job_finder_agent(user_profile=None)`**
```python
# Before
agent = create_job_finder_agent()

# After (automatic profile loading)
agent = create_job_finder_agent()  # Uses active profile

# Or explicit profile
from config.profile_manager import ProfileManager
pm = ProfileManager()
profile = pm.load_profile('example')
agent = create_job_finder_agent(profile)
```

### 2. Imports

**Models are now in a package:**
```python
# Before
from models import JobPosting, JobSearchOutput

# After (same import, different structure)
from models import JobPosting, JobSearchOutput

# New: User profile models
from models import UserProfile, SearchCriteria
```

### 3. Settings

**New environment variable:**
```bash
# In .env file
ACTIVE_PROFILE=seray  # Set which profile to use
```

**Deprecated (but still available for backward compatibility):**
```python
from config.settings import USER_PROFILE  # Still works, but deprecated
```

**New way:**
```python
from config.settings import get_active_user_profile
profile = get_active_user_profile()  # Returns UserProfile object
```

## Migration Steps

### For Existing Users

1. **No immediate action required** - The system is backward compatible
2. Your existing configuration has been migrated to `profiles/seray.json`
3. The default `ACTIVE_PROFILE=seray` is set automatically

### To Create a Custom Profile

1. **Copy the example:**
   ```bash
   cp profiles/seray.json profiles/yourname.json
   ```

2. **Edit your profile:**
   - Update `name`, `email`, `profile_id`
   - Modify `role_variations` for your target roles
   - Adjust `location_prefs` for your preferred locations
   - Set `experience` range and seniority preferences
   - Configure `languages` requirements
   - Set `posting_recency_days` and job count targets

3. **Activate your profile:**
   ```bash
   export ACTIVE_PROFILE=yourname
   # or add to .env file: ACTIVE_PROFILE=yourname
   ```

### For Developers

If you have custom code using the old functions:

```python
# Old code
from job_agents.job_finder_agent import create_job_finder_agent, score_job_match
agent = create_job_finder_agent()
score = score_job_match(job)

# New code
from config.settings import get_active_user_profile
from job_agents.job_finder_agent import create_job_finder_agent, score_job_match

profile = get_active_user_profile()
agent = create_job_finder_agent(profile)  # or just create_job_finder_agent()
score = score_job_match(job, profile)
```

## Benefits

✅ **Multi-user support**: Multiple people can have their own profiles
✅ **Easy A/B testing**: Test different search criteria without code changes
✅ **Type safety**: Pydantic models validate all configurations
✅ **Version control**: Profile configs are in JSON, easy to track changes
✅ **Reusability**: Same codebase works for different job search scenarios
✅ **No hardcoded values**: All search parameters are configurable

## Testing

Verify your setup:

```bash
# Test profile loading
python3 -c "
from config.settings import get_active_user_profile
profile = get_active_user_profile()
print(f'Active profile: {profile.name}')
print(f'Target roles: {profile.search_criteria.role_variations}')
"

# Test instruction generation
python3 -c "
from job_agents.job_finder_agent import build_job_search_instructions
from config.settings import get_active_user_profile

profile = get_active_user_profile()
instructions = build_job_search_instructions(profile)
print(f'Instructions generated: {len(instructions)} characters')
"
```

## Support

See `profiles/README.md` for detailed profile configuration documentation.

For questions or issues, refer to the profile examples in the `profiles/` directory.
