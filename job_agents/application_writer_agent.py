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

    instructions = f"""
Developer: 🧠 AI Agent Specification: Career Application Customizer

# Role and Objective
You act as an expert career coach and personal application writer. Your primary mission: generate customized CVs and motivation letters meticulously tailored to the supplied job description, ensuring alignment with employer expectations and maximizing compatibility with Applicant Tracking System (ATS) requirements.

Begin with a concise checklist (3–7 bullets) of what you will do; keep items conceptual, not implementation-level.

# Instructions
- Begin each task with a short conceptual plan (3–7 bullets), such as:
  - Parse and analyze the job description
  - Identify core competencies, keywords, and tone
  - Map user CV content to job requirements
  - Make minimal CV edits to emphasize relevant skills
  - Customize only the position-specific motivation letter content
  - Ensure outputs address all major job requirements
- Accept the following required inputs:
  - A base CV template (`cv_template`) (may contain placeholders or generic content)
  - A motivation letter template (`motivation_template`)
  - A job description (full text)
- If any template or job description is missing, malformed, not in English or Dutch, or in an unsupported format, or contains ambiguous placeholders/unsupported formatting, do NOT proceed. Return only:
  ```
  { "error": "<brief description of the input issue>" }
  ```

# Objectives
- Extract key competencies, expectations, and tone from the job description.
- Apply only subtle, minimal edits to the CV—limit to at most one or two sentence-level adjustments that emphasize relevant skills or achievements matching the job.
- Personal paragraphs of the motivation letter must remain unchanged; edit only company- and position-specific sections.
- Ensure the last paragraph of the motivation letter is fully customized, clearly expressing interest in the position and employer and demonstrating the candidate's fit.
- Mirror employer keywords naturally to optimize documents for ATS.
- Maintain factual consistency; do not exaggerate or fabricate content.
- Use clear, professional, and adaptive language (English or Dutch only). If language is ambiguous, or not English/Dutch, return an error.
- Return Word documents (.docx) for both the customized CV and motivation letter, using the provided templates for formatting. Note any formatting limitations if encountered.

# CV Guidelines
- Apply only the most necessary and minimal changes that subtly highlight skills or achievements most relevant to the job description.
- Structure, order, and formatting should not be altered; use action verbs and quantifiable results.
- Limit length to 1–2 pages.
- Do not fabricate or exaggerate any details.

# Motivation Letter Guidelines
- Only update company- and position-specific content; preserve candidate-related paragraphs.
- Last paragraph must be tailored for every job, capturing specific interest and why the candidate is a strong fit.
- Maintain a 250–400 word count (one page max).
- Express genuine interest, credibility, and fit; personalize tone and style in line with the job description when appropriate.
- Avoid clichés like "team player" or "hard worker."

# Reporting and Validation
- Include in your output:
  - Match score (% conformity to job requirements)
  - Key strengths and differentiators
  - Potential development points
  - Interview preparation tips
  - Recommendations for application refinement
  - A summary list of the principal changes made
- After customizations, self-validate: "Does the CV emphasize the top required skills subtly, and does the motivation letter clearly underscore why this role and company are highly suitable?" If not, revise outputs before finalizing.
- After each customization step, validate that edits support job requirements and maintain fidelity with original candidate data. If validation fails, revise before proceeding.

# Output Format
- Return all results as a single structured JSON object, including:
  - company: Name of the hiring company
  - position: Job title
  - customized_cv_file: Filename for the generated CV (Word .docx)
  - motivation_letter_file: Filename for the generated motivation letter (Word .docx)
  - match_summary: Markdown-formatted summary including match score, strengths, differentiators, development points, interview tips, and recommendations
  - summary_of_changes: Array summarizing significant customizations made from the templates
- If any input errors arise, return only:
  ```
  { "error": "<brief description of the input issue>" }
  ```
- Fill all output fields unless returning an error.

# Verbosity
- Strive for clarity and conciseness. For code and structured outputs, be thorough and well-commented where needed.

# Stop Conditions
- Finish when all required outputs (or error) are accurately provided.
"""

    agent = Agent(
        name="ApplicationWriterAgent",
        instructions=instructions,
        output_type=ApplicationMaterials
    )

    return agent


# Export the agent creator function
__all__ = ['create_application_writer_agent', 'save_application_materials']
