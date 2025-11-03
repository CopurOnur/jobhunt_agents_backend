"""
Job URL Scraper - Extracts real, working URLs from job boards.
Uses targeted scraping to find specific jobs and extract their actual URLs.
"""

import asyncio
import re
from typing import Optional, Dict, Any
from urllib.parse import urlparse, parse_qs, quote_plus
import logging

# Playwright will be imported conditionally
try:
    from playwright.async_api import async_playwright, Browser, Page, TimeoutError as PlaywrightTimeoutError
    PLAYWRIGHT_AVAILABLE = True
except ImportError:
    PLAYWRIGHT_AVAILABLE = False
    print("⚠️  Playwright not installed. Job URL scraping will be disabled.")
    print("   Install with: pip install playwright && playwright install chromium")


logger = logging.getLogger(__name__)


def is_valid_job_url(url: str) -> bool:
    """
    Validate if a URL is a direct job posting link (not a search results page).

    Args:
        url: URL to validate

    Returns:
        True if URL appears to be a valid job posting link
    """
    if not url or url == "URL_NOT_AVAILABLE":
        return False

    url_lower = url.lower()

    # Reject search result page patterns
    invalid_patterns = [
        '/vacatures',           # Indeed Netherlands search results
        '/jobs-srch',           # Glassdoor search results
        'jobs?q=',              # Generic search query
        'search/jobs',          # LinkedIn/other search pages
        '…',                    # Truncated URLs
        'see listing',          # Not a URL, just a note
        'see job',
    ]

    for pattern in invalid_patterns:
        if pattern in url_lower:
            return False

    # Check for placeholder job IDs
    if 'glassdoor.com' in url_lower:
        parsed = urlparse(url)
        query_params = parse_qs(parsed.query)
        job_id = query_params.get('jl', [None])[0]

        # Common placeholder IDs used by AI when it doesn't know the real ID
        placeholder_ids = ['123456', '654321', '789012', '345678', '901234', '567890']
        if job_id in placeholder_ids:
            return False

    # Accept valid patterns
    valid_patterns = [
        'indeed.com/viewjob?jk=',           # Indeed job view
        'indeed.com/rc/clk?jk=',            # Indeed redirect link
        'glassdoor.com/job-listing/',       # Glassdoor job listing
        'linkedin.com/jobs/view/',          # LinkedIn job view
        'careers.',                         # Company career pages
        '/career/',                         # Company career pages
        '/jobs/',                           # Company job pages
    ]

    for pattern in valid_patterns:
        if pattern in url_lower:
            return True

    # If URL is from a known job aggregator but doesn't match patterns, reject
    job_boards = ['indeed.com', 'glassdoor.com', 'linkedin.com']
    if any(board in url_lower for board in job_boards):
        return False

    # Otherwise accept (could be company website)
    return True


async def scrape_indeed_job_url(
    browser: Browser,
    job_title: str,
    company_name: str,
    location: str = "Netherlands"
) -> Optional[str]:
    """
    Search Indeed for a specific job and extract the real URL.

    Args:
        browser: Playwright browser instance
        job_title: Job title to search for
        company_name: Company name
        location: Location (default: Netherlands)

    Returns:
        Real Indeed job URL or None if not found
    """
    page = await browser.new_page()

    try:
        # Construct search query for specific job
        search_query = f'"{job_title}" "{company_name}"'
        search_url = f'https://nl.indeed.com/jobs?q={quote_plus(search_query)}&l={quote_plus(location)}'

        logger.info(f"Scraping Indeed for: {job_title} at {company_name}")

        await page.goto(search_url, wait_until='domcontentloaded', timeout=15000)

        # Wait for job results to load
        await page.wait_for_selector('.jobsearch-ResultsList', timeout=10000)

        # Find job cards
        job_cards = page.locator('.job_seen_beacon')

        # Check if any jobs found
        count = await job_cards.count()
        if count == 0:
            logger.warning(f"No Indeed jobs found for {job_title} at {company_name}")
            return None

        # Get the first job card (most relevant)
        first_job = job_cards.first

        # Extract job ID from data attribute
        job_id = await first_job.get_attribute('data-jk')

        if job_id:
            real_url = f'https://nl.indeed.com/viewjob?jk={job_id}'
            logger.info(f"✅ Found Indeed URL: {real_url}")
            return real_url
        else:
            logger.warning(f"Job card found but no job ID for {job_title}")
            return None

    except PlaywrightTimeoutError:
        logger.error(f"Timeout scraping Indeed for {job_title}")
        return None
    except Exception as e:
        logger.error(f"Error scraping Indeed: {e}")
        return None
    finally:
        await page.close()


async def scrape_glassdoor_job_url(
    browser: Browser,
    job_title: str,
    company_name: str,
    location: str = "Netherlands"
) -> Optional[str]:
    """
    Search Glassdoor for a specific job and extract the real URL.

    Args:
        browser: Playwright browser instance
        job_title: Job title to search for
        company_name: Company name
        location: Location (default: Netherlands)

    Returns:
        Real Glassdoor job URL or None if not found
    """
    page = await browser.new_page()

    try:
        # Construct search query
        search_query = f'{job_title} {company_name}'
        search_url = f'https://www.glassdoor.com/Job/netherlands-{quote_plus(job_title)}-jobs-SRCH_IL.0,11_IN178_KO12,{12+len(job_title)}.htm'

        logger.info(f"Scraping Glassdoor for: {job_title} at {company_name}")

        await page.goto(search_url, wait_until='domcontentloaded', timeout=15000)

        # Wait for job listings
        await page.wait_for_selector('[data-test="jobListing"]', timeout=10000)

        # Find job listings
        job_listings = page.locator('[data-test="jobListing"]')

        count = await job_listings.count()
        if count == 0:
            logger.warning(f"No Glassdoor jobs found for {job_title} at {company_name}")
            return None

        # Click the first job to get its URL
        first_job = job_listings.first

        # Try to find the link within the job listing
        job_link = first_job.locator('a[data-test="job-link"]').first

        if await job_link.count() > 0:
            href = await job_link.get_attribute('href')

            if href:
                # Construct full URL if relative
                if href.startswith('/'):
                    real_url = f'https://www.glassdoor.com{href}'
                else:
                    real_url = href

                logger.info(f"✅ Found Glassdoor URL: {real_url}")
                return real_url

        logger.warning(f"Job listing found but no link for {job_title}")
        return None

    except PlaywrightTimeoutError:
        logger.error(f"Timeout scraping Glassdoor for {job_title}")
        return None
    except Exception as e:
        logger.error(f"Error scraping Glassdoor: {e}")
        return None
    finally:
        await page.close()


async def scrape_job_url(
    job_title: str,
    company_name: str,
    source_url: str,
    location: str = "Netherlands"
) -> Optional[str]:
    """
    Main function to scrape a job URL from the appropriate job board.

    Args:
        job_title: Job title
        company_name: Company name
        source_url: Original URL from WebSearchTool (to determine which board to scrape)
        location: Location for search

    Returns:
        Real job URL or None if not found
    """
    if not PLAYWRIGHT_AVAILABLE:
        logger.warning("Playwright not available, skipping URL scraping")
        return None

    # Determine which job board to scrape based on source URL
    source_lower = source_url.lower()

    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=True)

        try:
            if 'indeed' in source_lower:
                return await scrape_indeed_job_url(browser, job_title, company_name, location)
            elif 'glassdoor' in source_lower:
                return await scrape_glassdoor_job_url(browser, job_title, company_name, location)
            else:
                logger.info(f"Source {source_url} is not Indeed or Glassdoor, skipping scraping")
                return None
        finally:
            await browser.close()


async def enrich_jobs_with_urls(jobs: list[Dict[str, Any]], location: str = "Netherlands") -> list[Dict[str, Any]]:
    """
    Enrich a list of jobs with real URLs by scraping job boards.
    Only scrapes jobs with invalid URLs.

    Args:
        jobs: List of job dictionaries with 'title', 'company', 'url' fields
        location: Location for job search

    Returns:
        List of jobs with enriched URLs
    """
    if not PLAYWRIGHT_AVAILABLE:
        logger.warning("Playwright not available. Jobs will keep original URLs.")
        return jobs

    enriched_jobs = []
    jobs_to_scrape = []

    # Identify which jobs need URL enrichment
    for job in jobs:
        if is_valid_job_url(job.get('url', '')):
            # URL is already valid, keep as-is
            enriched_jobs.append(job)
        else:
            # URL needs enrichment
            jobs_to_scrape.append(job)

    if not jobs_to_scrape:
        logger.info("All job URLs are valid, no scraping needed")
        return enriched_jobs

    logger.info(f"Scraping URLs for {len(jobs_to_scrape)} jobs with invalid URLs...")

    # Scrape URLs for jobs that need them
    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=True)

        try:
            for job in jobs_to_scrape:
                title = job.get('title', '')
                company = job.get('company', '')
                original_url = job.get('url', '')

                # Try to scrape real URL
                real_url = None

                if 'indeed' in original_url.lower():
                    real_url = await scrape_indeed_job_url(browser, title, company, location)
                elif 'glassdoor' in original_url.lower():
                    real_url = await scrape_glassdoor_job_url(browser, title, company, location)

                # Update job with real URL or mark as unavailable
                if real_url:
                    job['url'] = real_url
                    job['url_verified'] = True
                else:
                    job['url'] = "URL_NOT_AVAILABLE"
                    job['url_verified'] = False
                    job['url_note'] = "Direct job link could not be found. Search manually on job board."

                enriched_jobs.append(job)

                # Small delay to avoid rate limiting
                await asyncio.sleep(1)

        finally:
            await browser.close()

    logger.info(f"✅ URL enrichment complete. {len(enriched_jobs)} jobs processed.")

    return enriched_jobs


# Export main functions
__all__ = [
    'is_valid_job_url',
    'scrape_job_url',
    'enrich_jobs_with_urls',
    'PLAYWRIGHT_AVAILABLE'
]
