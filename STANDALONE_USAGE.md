# Standalone Interactive Application Writer

## Overview

The Standalone Interactive Application Writer allows you to customize your CV and motivation letter for specific job applications through an interactive chat interface. You provide your base materials (CV and motivation letter), then the AI agent customizes them for a specific job and allows you to refine them through conversation.

## Features

- **User-Provided Materials**: Use your own CV and motivation letter as the base
- **Job-Specific Customization**: Agent tailors your materials to match job requirements
- **Interactive Refinement**: Chat with the agent to make iterative improvements
- **Session Persistence**: All conversations are saved with SQLite sessions
- **Full History**: Session history is saved alongside your materials

## Installation

Ensure you have the required dependencies:

```bash
pip install agents pydantic python-dotenv
```

Make sure your `.env` file has your OpenAI API key:

```
OPENAI_API_KEY=your_api_key_here
```

## Usage

### Running the Script

```bash
cd job_application_flow
python3 standalone_application_writer.py
```

### Workflow

#### 1. Load Your Base Materials

You have two options:

**Option A: Load from files**
```
Choose how to provide your materials:
1. Load from files
2. Paste text directly

Your choice (1 or 2): 1

Path to your CV file: /path/to/my_cv.md
Path to your motivation letter file: /path/to/my_letter.md
```

**Option B: Paste text directly**
```
Your choice (1 or 2): 2

📝 Paste your CV (press Ctrl+D or Ctrl+Z when done):
[Paste your CV content here]
[Press Ctrl+D (Unix/Mac) or Ctrl+Z (Windows) when done]

📝 Paste your motivation letter (press Ctrl+D or Ctrl+Z when done):
[Paste your letter content here]
[Press Ctrl+D (Unix/Mac) or Ctrl+Z (Windows) when done]
```

#### 2. Provide Job Information

```
Company name: TechCorp Inc
Position title: Senior Learning Designer

📝 Paste the job description (press Ctrl+D or Ctrl+Z when done):
[Paste the full job description]
[Press Ctrl+D (Unix/Mac) or Ctrl+Z (Windows) when done]
```

#### 3. Review Generated Materials

The agent will generate:
- Customized CV
- Customized motivation letter
- Match summary (with match score and recommendations)

All three documents will be displayed in the terminal.

#### 4. Refine Through Chat

You can now chat with the agent to make refinements:

```
💬 You: Make the CV more technical

💬 You: Emphasize my leadership experience in the motivation letter

💬 You: Shorten the motivation letter to 300 words

💬 You: Add more about my experience with educational technology
```

**Special Commands:**
- `show` - Display current materials again
- `save` - Save materials and exit
- `quit` - Exit without saving

#### 5. Save and Exit

When satisfied with your materials:

```
💬 You: save
```

Your materials will be saved to:
```
storage/applications/YYYY-MM-DD/company_name/
  ├── customized_cv_company_name.md
  ├── motivation_letter_company_name.md
  ├── match_summary_company_name.md
  └── session_history.json
```

## Example Session

```bash
$ python3 standalone_application_writer.py

================================================================================
INTERACTIVE APPLICATION WRITER
Customize your CV and motivation letter for specific job applications
================================================================================

📄 Loading Your Base Materials

Choose how to provide your materials:
1. Load from files
2. Paste text directly

Your choice (1 or 2): 1

📁 Enter file paths:

Path to your CV file: my_cv.md
Path to your motivation letter file: my_letter.md

✅ Materials loaded successfully!
   CV: 2453 characters
   Motivation Letter: 876 characters

🤖 Initializing AI Agent...

✅ Agent initialized and ready!

================================================================================
JOB INFORMATION
================================================================================

Company name: EdTech Solutions
Position title: Learning Experience Designer

📝 Paste the job description (press Ctrl+D or Ctrl+Z when done):

[Job description content...]

✅ Job information captured!
   Company: EdTech Solutions
   Position: Learning Experience Designer
   Description: 1543 characters

🔄 Generating customized application materials...

✅ Materials generated successfully!

[Generated materials displayed...]

================================================================================
REFINEMENT MODE
================================================================================

You can now chat with the agent to refine your materials.
Examples:
  - 'Make the CV more technical'
  - 'Emphasize my leadership experience'
  - 'Shorten the motivation letter'
  - 'Add more about project management skills'

Type 'save' to save and exit, 'show' to display current materials,
or 'quit' to exit without saving.

💬 You: Make the motivation letter more enthusiastic about educational innovation

🔄 Processing your request...

✅ Materials updated!

[Updated materials displayed...]

💬 You: save

💾 Saving application materials...

✅ Saved application materials to storage/applications/2025-10-24/edtech_solutions

✅ All materials saved successfully!

📁 Output directory: storage/applications/2025-10-24/edtech_solutions
   CV: storage/applications/2025-10-24/edtech_solutions/customized_cv_edtech_solutions.md
   Motivation Letter: storage/applications/2025-10-24/edtech_solutions/motivation_letter_edtech_solutions.md
   Match Summary: storage/applications/2025-10-24/edtech_solutions/match_summary_edtech_solutions.md
   Session History: storage/applications/2025-10-24/edtech_solutions/session_history.json

👋 Thank you for using Interactive Application Writer!
```

## Tips for Best Results

1. **Prepare Quality Base Materials**: Ensure your base CV and motivation letter are comprehensive and well-written
2. **Detailed Job Descriptions**: Provide complete job descriptions for better customization
3. **Specific Refinement Requests**: Be clear about what you want to change
4. **Iterative Approach**: Make refinements one at a time for better control
5. **Review Before Saving**: Use `show` command to review materials before saving

## Architecture

### Key Components

1. **InteractiveApplicationWriter**: Main CLI class that orchestrates the workflow
2. **create_interactive_application_writer_agent()**: Creates an agent with user materials embedded in instructions
3. **SQLiteSession**: Maintains conversation context across multiple interactions
4. **ApplicationMaterials**: Pydantic model for structured output

### Conversation Flow

```
User Materials → Agent Instructions → Initial Generation → Refinement Loop → Save
     ↓                                        ↓                    ↓
  Base CV/Letter                        Customized Materials   Updated Materials
```

The agent maintains context throughout the session, allowing for natural conversation and iterative refinements.

## Troubleshooting

**Issue**: Agent fails to generate materials
- **Solution**: Check that your OpenAI API key is set correctly in `.env`

**Issue**: Materials don't match job requirements well
- **Solution**: Provide more detailed job description and use refinement chat

**Issue**: Can't paste text (Ctrl+D not working)
- **Solution**:
  - On Mac/Linux: Use Ctrl+D
  - On Windows: Use Ctrl+Z then Enter
  - Alternative: Use file loading option instead

**Issue**: Session history not saving
- **Solution**: Ensure `storage/` directory exists and is writable

## Advanced Usage

### Programmatic Usage

You can also use the components programmatically:

```python
import asyncio
from agents import Runner, SQLiteSession
from job_agents.application_writer_agent import (
    create_interactive_application_writer_agent,
    load_user_materials_from_file
)

async def customize_application():
    # Load materials
    cv, letter = load_user_materials_from_file("my_cv.md", "my_letter.md")

    # Create agent
    agent = create_interactive_application_writer_agent(cv, letter)

    # Create session
    session = SQLiteSession(session_id="my_session", db_path="storage/sessions.db")

    # Run generation
    result = await Runner.run(
        agent,
        "Generate materials for Software Engineer at Google...",
        session=session
    )

    materials = result.final_output_as(ApplicationMaterials)
    print(materials.customized_cv)

asyncio.run(customize_application())
```

## Related Files

- [standalone_application_writer.py](standalone_application_writer.py) - Main CLI script
- [job_agents/application_writer_agent.py](job_agents/application_writer_agent.py) - Agent creation and helpers
- [models/job_models.py](models/job_models.py) - Data models
