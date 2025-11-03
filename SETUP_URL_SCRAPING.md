# Job URL Scraping Setup Guide

## Overview

The job application system now includes **hybrid job URL extraction** that combines:
- **WebSearchTool** for fast job discovery (titles, companies, descriptions)
- **Playwright web scraping** for extracting real, working job URLs

This ensures that job postings have actual clickable links instead of search result page URLs.

## Installation

### 1. Install Playwright

```bash
# Install the Python package
pip install playwright

# Install browser binaries (Chromium)
playwright install chromium
```

### 2. Verify Installation

```bash
python -c "from playwright.async_api import async_playwright; print('Playwright installed successfully')"
```

If you see the success message, you're ready to go!

## Configuration

The scraping feature is controlled by environment variables in your `.env` file:

```bash
# Enable/disable URL scraping (default: true)
ENABLE_URL_SCRAPING=true

# Maximum retry attempts per job (default: 2)
MAX_SCRAPING_RETRIES=2

# Timeout for page loads in milliseconds (default: 15000)
SCRAPING_TIMEOUT_MS=15000
```

## How It Works

### Workflow

1. **WebSearchTool searches** for jobs matching your profile
   - Fast discovery across multiple job boards
   - Extracts job titles, companies, descriptions, snippets

2. **URL validation** checks which URLs are valid
   - Rejects search result page URLs (e.g., `/vacatures`, `/jobs-SRCH`)
   - Rejects placeholder job IDs (123456, 654321, etc.)
   - Accepts valid patterns (e.g., `indeed.com/viewjob?jk=`)

3. **Targeted scraping** for jobs with invalid URLs
   - Opens job board search for specific job + company
   - Extracts real job ID from the search results
   - Constructs proper job posting URL

4. **Merge results** with enriched URLs
   - Jobs with valid URLs keep original URLs
   - Jobs with invalid URLs get scraped URLs
   - Jobs that couldn't be found get marked as "URL_NOT_AVAILABLE"

### Supported Job Boards

Currently supports scraping for:
- ✅ **Indeed** (nl.indeed.com)
- ✅ **Glassdoor** (glassdoor.com)
- 🔄 **LinkedIn** (coming soon)

Other job boards (company career pages, etc.) will keep their original URLs if already valid.

## Graceful Degradation

The system works even without Playwright:

- **With Playwright**: Jobs get real, working URLs via scraping
- **Without Playwright**: Jobs keep original URLs from WebSearchTool (may be search pages)
- **Scraping fails**: Job is marked with `url: "URL_NOT_AVAILABLE"` and a note

## Usage

No code changes needed! The scraping happens automatically when you run a job search:

```bash
# Start the backend
cd job_application_flow
uvicorn app:app --reload

# Or run workflow directly
python workflow.py --once
```

You'll see log messages like:
```
🔍 Enriching job URLs with targeted scraping...
Scraping Indeed for: Learning Designer at Company Name
✅ Found Indeed URL: https://nl.indeed.com/viewjob?jk=abc123def456
✅ URL enrichment complete. 10 jobs processed.
```

## Troubleshooting

### Playwright not found

```
⚠️ Playwright not installed. Job URL scraping will be disabled.
```

**Solution**: Install Playwright:
```bash
pip install playwright
playwright install chromium
```

### Timeout errors

```
Timeout scraping Indeed for Learning Designer
```

**Solution**: Increase timeout in `.env`:
```bash
SCRAPING_TIMEOUT_MS=30000  # 30 seconds
```

### Rate limiting

If you're scraping many jobs and hit rate limits:

1. Reduce the number of jobs returned by the agent
2. The scraper already includes 1-second delays between jobs
3. Consider using a VPN or proxy (advanced)

### URLs still not working

Check the saved job postings in `storage/job_postings/`:
- Look for `"url_verified": true` fields
- Check `"url_note"` for explanation if URL unavailable
- Manually verify the job still exists on the job board

## Performance

**Typical scraping time**:
- WebSearchTool search: ~10-30 seconds
- Scraping 10 jobs: ~15-30 seconds
- **Total**: ~25-60 seconds for complete job search

**Without scraping**:
- WebSearchTool search: ~10-30 seconds
- **Total**: ~10-30 seconds

The extra time is worth it for working URLs!

## Advanced Configuration

### Disable scraping temporarily

Set in `.env`:
```bash
ENABLE_URL_SCRAPING=false
```

### Scrape only specific job boards

Edit `job_scraper.py` to customize which sources trigger scraping:

```python
# In scrape_job_url function
if 'indeed' in source_lower:
    return await scrape_indeed_job_url(...)
elif 'glassdoor' in source_lower:
    # Disable Glassdoor scraping
    return None
```

### Custom selectors

If job board HTML changes, update selectors in `job_scraper.py`:

```python
# Indeed job cards
job_cards = page.locator('.jobsearch-ResultsList .job_seen_beacon')

# Glassdoor job listings
job_listings = page.locator('[data-test="jobListing"]')
```

## Data Structure

Jobs now include these additional fields:

```json
{
  "title": "Learning Designer",
  "company": "Example Company",
  "url": "https://nl.indeed.com/viewjob?jk=abc123",
  "url_verified": true,
  "url_note": null,
  "match_score": 85,
  ...
}
```

For jobs where scraping failed:
```json
{
  "url": "URL_NOT_AVAILABLE",
  "url_verified": false,
  "url_note": "Direct job link could not be found. Search manually on job board."
}
```

## Future Enhancements

Planned improvements:
- [ ] LinkedIn job scraping
- [ ] Parallel scraping for faster performance
- [ ] Retry logic with exponential backoff
- [ ] Cache scraped URLs to avoid re-scraping
- [ ] Support for more job boards (Monster, StepStone, etc.)
- [ ] Optional Selenium fallback for environments without Playwright

## Contributing

To add support for a new job board:

1. Create scraping function in `job_scraper.py`:
   ```python
   async def scrape_newboard_job_url(browser, job_title, company_name, location):
       # Implementation
       pass
   ```

2. Add to `enrich_jobs_with_urls` function:
   ```python
   elif 'newboard' in original_url.lower():
       real_url = await scrape_newboard_job_url(...)
   ```

3. Test with real job searches

4. Submit pull request!

## Support

If you encounter issues:
1. Check the logs for error messages
2. Verify Playwright is installed correctly
3. Try increasing timeout values
4. Open an issue with error details and example job URLs
