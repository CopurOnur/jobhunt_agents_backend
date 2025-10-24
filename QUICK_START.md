# Quick Start Guide - Standalone Application Writer

## Quick Setup

1. **Install dependencies:**
   ```bash
   pip install agents pydantic python-dotenv
   ```

2. **Set your OpenAI API key in `.env`:**
   ```
   OPENAI_API_KEY=your_api_key_here
   ```

3. **Run the interactive writer:**
   ```bash
   python3 standalone_application_writer.py
   ```

## Quick Workflow

### Step 1: Load Your Materials
```
Choose how to provide your materials:
1. Load from files
2. Paste text directly

Your choice: 1

Path to your CV file: example_cv.md
Path to your motivation letter file: example_motivation_letter.md
```

### Step 2: Enter Job Details
```
Company name: EdTech Innovations
Position title: Senior Learning Designer

📝 Paste the job description:
[Paste job description here]
[Press Ctrl+D when done]
```

### Step 3: Review Generated Materials
The agent generates:
- ✅ Customized CV
- ✅ Customized Motivation Letter
- ✅ Match Summary with score

### Step 4: Refine (Optional)
```
💬 You: Make it more technical
💬 You: Emphasize leadership experience
💬 You: save
```

## Commands During Chat

| Command | Action |
|---------|--------|
| `save` | Save materials and exit |
| `show` | Display current materials |
| `quit` | Exit without saving |
| Any text | Refine materials with that request |

## Example Refinement Requests

```
💬 "Make the CV highlight my technical skills more"
💬 "Shorten the motivation letter to 300 words"
💬 "Add more about my project management experience"
💬 "Make the tone more enthusiastic"
💬 "Focus on my leadership accomplishments"
💬 "Add keywords from the job description"
```

## Output Location

Materials are saved to:
```
storage/applications/{date}/{company_name}/
  ├── customized_cv_{company_name}.md
  ├── motivation_letter_{company_name}.md
  ├── match_summary_{company_name}.md
  └── session_history.json
```

## Example Files

Try it with the included example files:
- `example_cv.md` - Sample CV
- `example_motivation_letter.md` - Sample motivation letter

## Need Help?

- Full documentation: See [STANDALONE_USAGE.md](STANDALONE_USAGE.md)
- Issues: Check that your OpenAI API key is set correctly
- Tips: Be specific with refinement requests for best results

## What Makes This Different?

Unlike the automated workflow that generates applications for multiple jobs:

✅ **You provide your own CV and letter** - Uses your actual materials, not templates
✅ **Interactive refinement** - Chat to make changes until perfect
✅ **Single job focus** - Deep customization for one specific application
✅ **Session persistence** - Conversation history saved with materials
✅ **Full control** - Review and refine before saving
