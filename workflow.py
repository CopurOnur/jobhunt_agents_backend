"""
Main workflow orchestrator for the job application flow using OpenAI Agents SDK.
Coordinates JobFinderAgent and ApplicationWriterAgent using Runner and async orchestration.
"""

import asyncio
from datetime import datetime
from typing import List, Dict, Any
import json
from pathlib import Path

from agents import Runner, SQLiteSession

from job_agents.job_finder_agent import (
    create_job_finder_agent,
    score_job_match,
    save_job_postings
)
from job_agents.application_writer_agent import (
    create_application_writer_agent,
    save_application_materials
)
from models import JobSearchOutput, ApplicationMaterials
from config.settings import get_active_user_profile


class JobApplicationWorkflow:
    """Orchestrates the job search and application generation workflow using OpenAI Agents SDK."""

    def __init__(self, session_id: str = None):
        """Initialize the workflow with agents and session."""
        self.job_finder = create_job_finder_agent()
        self.application_writer = create_application_writer_agent()
        self.user_profile = get_active_user_profile()
        # Create session with unique ID or use default
        if session_id is None:
            session_id = f"workflow_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
        self.session = SQLiteSession(session_id=session_id, db_path="storage/sessions.db")
        self.execution_log: List[Dict[str, Any]] = []

    async def run_once_for_api(self) -> Dict[str, Any]:
        """
        Run the workflow once and return structured results for API consumption.
        Async version using OpenAI Agents SDK Runner.

        Returns:
            Dictionary with job_postings, applications, summary, and metadata
        """
        try:
            # Step 1: Search for job postings
            search_prompt = """Search for job postings in the Netherlands that match the user profile.
Focus on Trainer, L&D Specialist, Learning Designer, and Experiential Learning Designer roles.
Return 8-12 high-quality job postings with all details."""

            job_search_result = await Runner.run(
                self.job_finder,
                search_prompt,
                session=self.session
            )

            # Extract structured output
            job_search_output: JobSearchOutput = job_search_result.final_output_as(JobSearchOutput)

            if not job_search_output or not job_search_output.jobs:
                return {
                    "success": False,
                    "error": "No jobs found",
                    "job_count": 0,
                    "applications_generated": 0,
                    "timestamp": datetime.now().isoformat()
                }

            # Add match scores to jobs
            jobs_with_scores = []
            for job in job_search_output.jobs:
                job_dict = job.model_dump()
                job_dict['match_score'] = score_job_match(job_dict, self.user_profile)
                jobs_with_scores.append(job_dict)

            # Save job postings
            save_job_postings(jobs_with_scores, job_search_output.search_date, self.user_profile)

            # Step 2: Generate applications for each job
            application_results = []
            for job in jobs_with_scores:
                try:
                    # Create prompt for application writer
                    app_prompt = f"""Generate customized application materials for this job posting:

Job Title: {job['title']}
Company: {job['company']}
Location: {job['location']}
Description: {job['description']}
Requirements: {', '.join(job.get('requirements', []))}
Skills: {', '.join(job.get('skills', []))}

Generate a customized CV, motivation letter, and match summary."""

                    app_result = await Runner.run(
                        self.application_writer,
                        app_prompt,
                        session=self.session
                    )

                    # Extract structured output
                    materials: ApplicationMaterials = app_result.final_output_as(ApplicationMaterials)

                    if materials:
                        # Save materials to files
                        file_paths = save_application_materials(materials, job['company'])

                        application_results.append({
                            "success": True,
                            "company": job['company'],
                            "position": job['title'],
                            **file_paths,
                            "timestamp": datetime.now().isoformat()
                        })
                    else:
                        application_results.append({
                            "success": False,
                            "company": job['company'],
                            "error": "Failed to generate materials"
                        })

                except Exception as e:
                    application_results.append({
                        "success": False,
                        "company": job.get('company', 'Unknown'),
                        "error": str(e)
                    })

            # Step 3: Generate summary
            successful_applications = [r for r in application_results if r.get("success")]
            summary = self._generate_summary(
                {"job_count": len(jobs_with_scores), "job_postings": jobs_with_scores},
                application_results
            )

            # Return structured result
            return {
                "success": True,
                "job_count": len(jobs_with_scores),
                "applications_generated": len(successful_applications),
                "job_postings": jobs_with_scores,
                "applications": application_results,
                "summary": summary,
                "timestamp": datetime.now().isoformat()
            }

        except Exception as e:
            return {
                "success": False,
                "error": str(e),
                "job_count": 0,
                "applications_generated": 0,
                "timestamp": datetime.now().isoformat()
            }

    async def run_job_search_only(self) -> Dict[str, Any]:
        """
        Run ONLY the job search (no application generation).
        Returns job postings with match scores for frontend display.

        Returns:
            Dictionary with job_postings and match scores
        """
        try:
            # Execute job search
            search_prompt = """Search for job postings in the Netherlands matching the user profile.
Focus on Trainer, L&D Specialist, Learning Designer, and Experiential Learning Designer roles.
Return 8-12 high-quality job postings."""

            job_search_result = await Runner.run(
                self.job_finder,
                search_prompt,
                session=self.session
            )

            # Extract structured output
            job_search_output: JobSearchOutput = job_search_result.final_output_as(JobSearchOutput)

            if not job_search_output or not job_search_output.jobs:
                return {
                    "success": False,
                    "error": "No jobs found",
                    "job_count": 0,
                    "job_postings": [],
                    "timestamp": datetime.now().isoformat()
                }

            # Add match scores
            jobs_with_scores = []
            for job in job_search_output.jobs:
                job_dict = job.model_dump()
                job_dict['match_score'] = score_job_match(job_dict, self.user_profile)
                jobs_with_scores.append(job_dict)

            # Save results
            save_job_postings(jobs_with_scores, job_search_output.search_date, self.user_profile)

            return {
                "success": True,
                "job_count": len(jobs_with_scores),
                "job_postings": jobs_with_scores,
                "timestamp": datetime.now().isoformat()
            }

        except Exception as e:
            return {
                "success": False,
                "error": str(e),
                "job_count": 0,
                "job_postings": [],
                "timestamp": datetime.now().isoformat()
            }

    async def run_application_generation(self, selected_jobs: List[Dict[str, Any]]) -> Dict[str, Any]:
        """
        Generate applications for ONLY the selected job postings.

        Args:
            selected_jobs: List of job posting dictionaries to generate applications for

        Returns:
            Dictionary with applications and summary
        """
        try:
            if not selected_jobs:
                return {
                    "success": False,
                    "error": "No jobs selected",
                    "applications_generated": 0,
                    "applications": [],
                    "timestamp": datetime.now().isoformat()
                }

            # Generate applications for selected jobs only
            application_results = []
            for job in selected_jobs:
                try:
                    app_prompt = f"""Generate customized application materials for this job:

Job Title: {job['title']}
Company: {job['company']}
Location: {job['location']}
Description: {job.get('description', '')}
Requirements: {', '.join(job.get('requirements', []))}
Skills: {', '.join(job.get('skills', []))}"""

                    app_result = await Runner.run(
                        self.application_writer,
                        app_prompt,
                        session=self.session
                    )

                    materials: ApplicationMaterials = app_result.final_output_as(ApplicationMaterials)

                    if materials:
                        file_paths = save_application_materials(materials, job['company'])
                        application_results.append({
                            "success": True,
                            "company": job['company'],
                            "position": job['title'],
                            **file_paths,
                            "timestamp": datetime.now().isoformat()
                        })
                    else:
                        application_results.append({
                            "success": False,
                            "company": job['company'],
                            "error": "Failed to generate materials"
                        })

                except Exception as e:
                    application_results.append({
                        "success": False,
                        "company": job.get('company', 'Unknown'),
                        "error": str(e)
                    })

            # Generate summary
            job_search_result = {
                "job_count": len(selected_jobs),
                "job_postings": selected_jobs
            }
            summary = self._generate_summary(job_search_result, application_results)

            # Count successful applications
            successful_applications = [r for r in application_results if r.get("success")]

            return {
                "success": True,
                "applications_generated": len(successful_applications),
                "applications": application_results,
                "summary": summary,
                "timestamp": datetime.now().isoformat()
            }

        except Exception as e:
            return {
                "success": False,
                "error": str(e),
                "applications_generated": 0,
                "applications": [],
                "timestamp": datetime.now().isoformat()
            }

    def _generate_summary(
        self,
        job_search_result: Dict[str, Any],
        application_results: List[Dict[str, Any]]
    ) -> str:
        """Generate a markdown summary of the workflow execution."""
        successful_applications = [r for r in application_results if r.get("success")]
        failed_applications = [r for r in application_results if not r.get("success")]

        summary = f"""
# Daily Job Search Summary

**Date:** {datetime.now().strftime('%Y-%m-%d')}
**Time:** {datetime.now().strftime('%H:%M:%S')}

## Results

- **Jobs Found:** {job_search_result.get('job_count', 0)}
- **Applications Generated:** {len(successful_applications)}
- **Failed Applications:** {len(failed_applications)}

## Job Postings

"""
        for result in successful_applications:
            summary += f"""
### {result.get('company')} - {result.get('position')}
- **CV:** `{result.get('cv_path')}`
- **Letter:** `{result.get('letter_path')}`
- **Summary:** `{result.get('summary_path')}`
"""

        if failed_applications:
            summary += "\n## Failed Applications\n"
            for result in failed_applications:
                summary += f"- {result.get('company', 'Unknown')}: {result.get('error')}\n"

        summary += f"""
## Next Steps

1. Review generated application materials in the storage/applications/ directory
2. Customize any materials that need personal touches
3. Submit applications through the respective job portals
4. Track application status and follow-ups

---
Generated by JobApplicationWorkflow (OpenAI Agents SDK)
"""
        return summary

    def _log_execution(self, event_type: str, data: Dict[str, Any]):
        """Log workflow execution events."""
        log_entry = {
            "timestamp": datetime.now().isoformat(),
            "event_type": event_type,
            "data": data
        }
        self.execution_log.append(log_entry)

        # Save to file
        log_file = Path("workflow_execution_log.json")
        with open(log_file, 'w', encoding='utf-8') as f:
            json.dump(self.execution_log, f, indent=2, ensure_ascii=False)

    # Sync wrappers for backward compatibility
    def run_once(self):
        """Run the workflow once (sync wrapper for async method)."""
        return asyncio.run(self.run_once_for_api())

    def run_daily_workflow(self):
        """Execute the complete workflow with console output (sync wrapper)."""
        print(f"\n{'='*60}")
        print(f"Starting Job Application Workflow - {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        print(f"{'='*60}\n")

        result = asyncio.run(self.run_once_for_api())

        if result.get("success"):
            print(f"\n✅ Workflow completed successfully!")
            print(f"   Jobs found: {result.get('job_count', 0)}")
            print(f"   Applications generated: {result.get('applications_generated', 0)}")
        else:
            print(f"\n❌ Workflow failed: {result.get('error')}")

        return result


def main():
    """Main entry point for the workflow."""
    import sys

    workflow = JobApplicationWorkflow()

    if len(sys.argv) > 1 and sys.argv[1] == "--once":
        # Run once for testing
        print("Running workflow once (test mode)...\n")
        workflow.run_once()
    else:
        # Run daily workflow
        print("Running daily workflow...\n")
        workflow.run_daily_workflow()


if __name__ == "__main__":
    main()
