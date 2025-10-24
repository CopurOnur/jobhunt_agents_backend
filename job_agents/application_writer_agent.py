"""
ApplicationWriterAgent - Generates customized CVs and motivation letters using OpenAI Agents SDK.
"""

from typing import Dict, Any
from datetime import datetime
from pathlib import Path

from agents import Agent
from pydantic import BaseModel

from config.settings import USER_PROFILE, APPLICATIONS_DIR, TEMPLATES_DIR
from models import ApplicationMaterials, ApplicationOutput


# Helper functions for file operations

def load_template(template_name: str) -> str:
    """
    Load a template file.

    Args:
        template_name: Name of template file (e.g., "base_cv.md")

    Returns:
        Template content as string
    """
    template_path = TEMPLATES_DIR / template_name

    if not template_path.exists():
        print(f"⚠️  Template {template_name} not found, using default structure")
        return get_default_template(template_name)

    with open(template_path, 'r', encoding='utf-8') as f:
        return f.read()


def get_default_template(template_name: str) -> str:
    """
    Return default template content if template file doesn't exist.

    Args:
        template_name: Name of template

    Returns:
        Default template string
    """
    if "cv" in template_name.lower():
        return """# Curriculum Vitae

## Personal Information
Name: {name}
Location: {location}

## Professional Summary
[To be customized]

## Experience
[To be customized]

## Education
[To be customized]

## Skills
[To be customized]
"""
    else:
        return """# Motivation Letter

Dear Hiring Manager,

[To be customized]

Sincerely,
{name}
"""


def save_application_materials(
    materials: ApplicationMaterials,
    company_name: str
) -> Dict[str, str]:
    """
    Save application materials to files.

    Args:
        materials: ApplicationMaterials model with CV, letter, and summary
        company_name: Company name for folder organization

    Returns:
        Dictionary with file paths
    """
    # Sanitize company name for filename
    safe_company = "".join(
        c if c.isalnum() or c in ('-', '_') else '_'
        for c in company_name
    ).lower()

    # Create output directory
    date_str = datetime.now().strftime("%Y-%m-%d")
    output_dir = APPLICATIONS_DIR / date_str / safe_company
    output_dir.mkdir(parents=True, exist_ok=True)

    # Save documents
    cv_path = output_dir / f"customized_cv_{safe_company}.md"
    letter_path = output_dir / f"motivation_letter_{safe_company}.md"
    summary_path = output_dir / f"match_summary_{safe_company}.md"

    with open(cv_path, 'w', encoding='utf-8') as f:
        f.write(materials.customized_cv)

    with open(letter_path, 'w', encoding='utf-8') as f:
        f.write(materials.motivation_letter)

    with open(summary_path, 'w', encoding='utf-8') as f:
        f.write(materials.match_summary)

    print(f"✅ Saved application materials to {output_dir}")

    return {
        "cv_path": str(cv_path),
        "letter_path": str(letter_path),
        "summary_path": str(summary_path),
        "output_directory": str(output_dir)
    }


# Create the ApplicationWriterAgent
def create_application_writer_agent() -> Agent:
    """
    Create and configure the ApplicationWriterAgent using OpenAI Agents SDK.

    Returns:
        Configured Agent instance
    """
    # Load templates
    cv_template = load_template("base_cv.md")
    motivation_template = load_template("base_motivation_letter.md")

    instructions = f"""You are an expert career coach and application writer. Your role is to create
customized CVs and motivation letters for job applications, ensuring they highlight relevant
experience and skills that match the job requirements.

USER PROFILE:
- Name: {USER_PROFILE.get('name')}
- Location: {USER_PROFILE.get('location')}
- Languages: {', '.join(USER_PROFILE.get('languages', []))}
- Focus Areas: {', '.join(USER_PROFILE.get('focus_roles', []))}

YOUR OBJECTIVES:
1. Analyze job descriptions to identify key requirements and desired skills
2. Customize the CV to emphasize relevant experience and achievements
3. Write compelling motivation letters that connect the candidate's background to the role
4. Maintain professional tone while showing personality and enthusiasm
5. Use specific examples and metrics where possible

GUIDELINES FOR CV:
- Keep to 1-2 pages, well-structured and easy to scan
- Use action verbs and quantifiable achievements
- Mirror keywords from the job description naturally
- Highlight experience relevant to the specific role
- Professional formatting in markdown

GUIDELINES FOR MOTIVATION LETTER:
- 250-400 words total
- Show genuine interest in the role and company
- Connect candidate's background to job requirements
- Demonstrate understanding of the company and position
- Maintain authenticity and honesty
- Professional yet personable tone

GUIDELINES FOR MATCH SUMMARY:
- Provide 5-7 bullet points analyzing the match
- Include estimated match score percentage
- List key strengths that align with the role
- Identify potential gaps or areas to address in interview
- Provide recommendations for tailoring the application

CV TEMPLATE:
{cv_template}

MOTIVATION LETTER TEMPLATE:
{motivation_template}

When given a job posting, generate all three documents (CV, motivation letter, and match summary)
and return them in a structured format.

OUTPUT FORMAT:
Return a JSON object with this structure:
{{
    "company": "Company Name",
    "position": "Job Title",
    "customized_cv": "Full CV content in markdown...",
    "motivation_letter": "Full letter content in markdown...",
    "match_summary": "Full summary in markdown..."
}}
"""

    agent = Agent(
        name="ApplicationWriterAgent",
        instructions=instructions,
        output_type=ApplicationMaterials
    )

    return agent


# Export the agent creator function
__all__ = ['create_application_writer_agent', 'save_application_materials']
