# Building an AI-Powered Job Application Assistant: A Full-Stack Journey with Multi-Agent Systems

*How I built an intelligent system that searches for jobs and generates personalized applications using OpenAI's Agents SDK, FastAPI, and Next.js*

---

## The Problem: Job Applications Are Time-Consuming

If you've ever been on the job hunt, you know the drill: spending hours customizing your CV and cover letter for each position, trying to highlight the right skills, and tailoring your experience to match what employers are looking for. For someone actively searching for roles—especially across multiple companies—this process becomes exhausting and repetitive.

I wanted to solve this problem not just for myself, but to create a tool that could help anyone streamline their job search. The goal? **An intelligent system that automatically finds relevant job postings and generates perfectly customized application materials for each one.**

---

## The Vision: Multi-Agent Collaboration

Instead of building a single monolithic AI system, I decided to take a **multi-agent approach**—inspired by how humans actually work. Think about it: in real life, you might have one person researching job opportunities while another person focuses on crafting compelling applications. Each specialist does what they do best.

That's exactly how I architected this system:

### 🔍 **The Job Finder Agent**
A specialized AI agent that acts as your personal job scout. It searches the web for relevant positions, filters them based on your criteria (location, experience level, languages, role type), and scores each job on how well it matches your profile.

### ✍️ **The Application Writer Agent**
Your personal career coach and copywriter. This agent takes your base CV and motivation letter, analyzes the job requirements, and generates customized versions that highlight your most relevant experience and skills for each specific position.

### 💬 **The Interactive Refinement System**
But here's where it gets really interesting: the system doesn't just generate materials and call it a day. It enables **conversational refinement**. Don't like how technical your CV sounds? Ask it to adjust the tone. Want to emphasize leadership experience? Just tell it. The agent iteratively refines your materials through natural conversation until they're perfect.

---

## The Tech Stack: Modern & Production-Ready

Building this required carefully selecting technologies that would enable both powerful AI capabilities and a smooth user experience.

### Backend: Python + FastAPI + OpenAI Agents SDK

The backend is where the magic happens. I chose **FastAPI** for its async capabilities, automatic API documentation, and type safety—perfect for handling multiple concurrent job searches and background task processing.

The real star of the show is **OpenAI's Agents SDK**, which provides:
- Multi-agent orchestration with persistent conversation memory
- Structured outputs using Pydantic models (type-safe AI responses!)
- Built-in tools like `WebSearchTool` for job searching
- Session management with SQLite for conversation continuity

Here's a glimpse of how clean the agent creation code looks:

```python
agent = Agent(
    name="ApplicationWriterAgent",
    instructions=dynamic_instructions,
    output_type=ApplicationMaterials  # Type-safe AI output!
)

result = await Runner.run(agent, user_request, session=session)
materials = result.final_output_as(ApplicationMaterials)
```

### Frontend: Next.js 14 + React + TypeScript

For the user interface, I went with **Next.js 14** (using the new App Router), **React 18**, and **TypeScript** for a modern, type-safe frontend experience.

The state management strategy was crucial. I used **TanStack React Query** for server state, which provides:
- Automatic caching and refetching
- Smart polling that restarts when needed
- Background updates without blocking the UI
- Optimistic updates for a snappy user experience

**Tailwind CSS** made styling a breeze, letting me rapidly build a clean, responsive interface without wrestling with CSS files.

---

## The Architecture: How It All Fits Together

### The API Flow

```
User → Frontend (Next.js) → REST API (FastAPI) → Multi-Agent System → AI Processing
                                                        ↓
                                                  SQLite Sessions
                                                        ↓
                                            File System Storage
```

### Background Task Processing

One of the key architectural decisions was handling long-running AI tasks. Generating customized applications can take 30-60 seconds per job, so I implemented:

1. **Async background tasks** using FastAPI's BackgroundTasks
2. **Polling-based status updates** where the frontend checks for completion
3. **In-memory job status store** for fast lookups (would use Redis in production)

Here's the flow:
```python
@app.post("/api/writer/start")
async def start_writer_session(request, background_tasks: BackgroundTasks):
    session_id = str(uuid.uuid4())

    # Store initial status
    job_status_store[session_id] = {
        "status": "pending",
        "chat_history": [{"role": "system", "content": "Generating..."}]
    }

    # Process in background
    background_tasks.add_task(run_writer_task, session_id, request)

    return {"session_id": session_id, "status": "pending"}
```

The frontend then polls every 2 seconds until the status becomes "completed":

```typescript
useQuery({
  queryKey: ['writerSession', sessionId],
  queryFn: () => writerApi.getSession(sessionId),
  refetchInterval: (query) => {
    const data = query.state.data;
    if (data?.status === 'completed' || data?.status === 'failed') {
      return false; // Stop polling
    }
    return 2000; // Poll every 2 seconds
  }
})
```

---

## The Iterative Refinement Feature: Conversational AI

One of the most challenging—and rewarding—features to build was the **iterative refinement system**. This lets users have a natural conversation with the AI to improve their application materials.

### The Problem We Solved

Initially, the system would generate materials and that was it. But users wanted control. They wanted to be able to say things like:
- "Make the CV more technical"
- "Shorten the motivation letter to 250 words"
- "Emphasize my leadership experience"

### The Solution: Backend-Stored Chat History

The key insight was that the **chat history needed to live on the backend**, not the frontend. Here's why:

1. **Conversation continuity**: The AI agent needs access to the full conversation history to provide context-aware refinements
2. **Session persistence**: Using SQLite sessions, the agent remembers previous interactions
3. **Accurate timestamps**: The backend tracks exactly when each message was processed

Here's how we store chat messages:

```python
# When user sends refinement
user_message = {
    "role": "user",
    "content": request.refinement_request,
    "timestamp": datetime.now().isoformat()
}
job_status_store[session_id]["chat_history"].append(user_message)

# After agent processes refinement
assistant_message = {
    "role": "assistant",
    "content": "I've updated the materials based on your request...",
    "timestamp": datetime.now().isoformat()
}
job_status_store[session_id]["chat_history"].append(assistant_message)
```

The frontend simply syncs with the backend chat history:

```typescript
useEffect(() => {
  if (sessionData?.chat_history) {
    setChatHistory(sessionData.chat_history);
  }
}, [sessionData?.chat_history]);
```

This architecture ensures the conversation is **always consistent**, **never out of sync**, and the AI has **full context** for each refinement request.

---

## User Profile System: Personalization at Scale

To make the system truly useful for different users, I built a **flexible profile system**. Each user can have their own JSON configuration file defining:

- **Role variations**: What job titles to search for (e.g., "Learning Designer", "Instructional Designer", "L&D Specialist")
- **Location preferences**: Countries, cities, and remote work options
- **Experience level**: Min/max years of experience
- **Language requirements**: Required languages and those to exclude
- **Search parameters**: Job posting recency, target number of jobs, etc.

Example profile structure:

```json
{
  "name": "name surname",
  "profile_id": "seray",
  "search_criteria": {
    "role_variations": ["Trainer", "Learning Designer", "L&D Specialist"],
    "location_prefs": {
      "country": "Netherlands",
      "cities": ["Amsterdam", "Rotterdam", "Utrecht"],
      "allow_remote": true
    },
    "experience": {
      "min_years": 0,
      "max_years": 5,
      "level": "junior"
    },
    "languages": [
      {"language": "English", "required": true},
      {"language": "Dutch", "required": false, "exclude_if_required": true}
    ]
  }
}
```

The system uses **Pydantic models** for validation, ensuring profiles are always correctly formatted:

```python
class UserProfile(BaseModel):
    name: str
    profile_id: str
    search_criteria: SearchCriteria

    model_config = ConfigDict(extra="forbid")  # Catch typos!
```

---

## Deployment: Docker + HuggingFace Spaces

Getting this project from local development to production required containerization. I created a **Dockerfile** optimized for HuggingFace Spaces:

```dockerfile
FROM python:3.12

# Security: non-root user
RUN useradd -m -u 1000 user
USER user

WORKDIR /app

COPY --chown=user ./requirements.txt .
RUN pip install --no-cache-dir --upgrade -r requirements.txt

COPY --chown=user . /app

# Create storage directories
RUN mkdir -p storage/job_postings storage/applications

EXPOSE 7860

CMD ["uvicorn", "app:app", "--host", "0.0.0.0", "--port", "7860"]
```

HuggingFace Spaces provides:
- **Free hosting** for the backend API
- **Automatic HTTPS** and domain
- **Environment variable management** for secrets
- **Build logs** and monitoring

---

## Challenges & Solutions

### Challenge 1: Polling Doesn't Restart After Refinement

**Problem**: When a refinement completed, the React Query polling would stop and never restart, so subsequent refinements wouldn't update the UI.

**Solution**: Manually trigger a refetch after sending a refinement request:

```typescript
const refineMaterials = async (request: string) => {
  await writerApi.refineSession(sessionId, { refinement_request: request });
  refetchSession(); // ← This restarts polling!
};
```

### Challenge 2: Agent Not Making Actual Changes

**Problem**: The agent would return success but materials weren't actually different.

**Solution**: Added detailed logging to track material changes:

```python
old_letter = old_materials.get("motivation_letter", "")
new_letter = materials.motivation_letter

print(f"   Old letter length: {len(old_letter)}")
print(f"   New letter length: {len(new_letter)}")
print(f"   Materials changed: {old_letter != new_letter}")
```

This helped us verify the agent was working correctly—it turned out to be a frontend display issue, not an agent problem!

### Challenge 3: Type Safety Across Stack

**Problem**: Keeping TypeScript types in sync with Python Pydantic models manually is error-prone.

**Solution**: Defined clear interface contracts and leveraged FastAPI's automatic OpenAPI schema generation. In the future, I could use tools like `datamodel-code-generator` to auto-generate TypeScript types from Pydantic models.

---

## What I Learned

### 1. Multi-Agent Systems Are Powerful
Breaking down complex tasks into specialized agents makes the system more maintainable and each agent more focused. It's easier to debug and improve a "job searcher" vs. trying to handle everything in one massive prompt.

### 2. Backend State Management Matters
Storing critical state (like chat history) on the backend rather than the frontend prevents sync issues and enables true conversation continuity.

### 3. Polling is Simple but Effective
While WebSockets or Server-Sent Events might be "cooler," polling with React Query is simple, reliable, and works great for this use case. Don't over-engineer.

### 4. Type Safety is Worth the Effort
Using Pydantic on the backend and TypeScript on the frontend caught countless bugs before they hit production. The upfront investment in types pays dividends.

### 5. User Experience Requires Iteration
The iterative refinement feature went through multiple redesigns based on actually using the system. Talking to real users (even if it's just yourself!) reveals UX issues you'd never anticipate.

---

## Future Improvements

There's always room to grow. Here are features I'd love to add:

- **Real job board integrations**: Connect to LinkedIn, Indeed, or Glassdoor APIs instead of web search
- **Backend authentication**: Replace client-side auth with JWT tokens and httpOnly cookies
- **Persistent database**: Replace in-memory store with PostgreSQL or MongoDB
- **Version comparison**: Show diffs between refinement iterations
- **Email notifications**: Alert users when new matching jobs are found
- **Analytics dashboard**: Track application success rates and improve agent prompts
- **Streaming responses**: Show materials as they're being generated (Server-Sent Events)

---

## Try It Yourself

The project is structured to be easily extensible. Want to adapt it for software engineering roles? Just create a new profile JSON:

```json
{
  "name": "Your Name",
  "profile_id": "yourname",
  "search_criteria": {
    "role_variations": ["Software Engineer", "Full Stack Developer", "Backend Engineer"],
    "location_prefs": {
      "country": "USA",
      "cities": ["San Francisco", "New York", "Remote"],
      "allow_remote": true
    }
  }
}
```

Set `ACTIVE_PROFILE=yourname` in your `.env` file and you're ready to go!

---

## The Tech Stack Summary

**Backend:**
- Python 3.13
- FastAPI (async REST API)
- OpenAI Agents SDK (multi-agent framework)
- Pydantic (data validation)
- SQLite (session persistence)
- Uvicorn (ASGI server)

**Frontend:**
- Next.js 14 (App Router)
- React 18
- TypeScript 5
- TanStack React Query (state management)
- Tailwind CSS (styling)
- Axios (HTTP client)

**Deployment:**
- Docker
- HuggingFace Spaces

---

## Conclusion: AI as a Collaborative Tool

This project reinforced my belief that the best AI systems are **collaborative**, not autonomous. The system doesn't replace human judgment—it augments it. Users maintain full control, making decisions about which jobs to apply to and how to refine their materials. The AI simply saves time and provides a strong starting point.

Building this taught me that **modern AI development is as much about software engineering as it is about prompts**. Clean architecture, type safety, proper state management, and good UX matter just as much as the AI model itself.

If you're building AI-powered applications, remember: **the AI is powerful, but the system design is what makes it useful.**

---

## Resources

- **OpenAI Agents SDK**: [github.com/openai/swarm](https://github.com/openai/swarm) (similar architecture)
- **FastAPI**: [fastapi.tiangolo.com](https://fastapi.tiangolo.com)
- **Next.js**: [nextjs.org](https://nextjs.org)
- **TanStack Query**: [tanstack.com/query](https://tanstack.com/query)
- **HuggingFace Spaces**: [huggingface.co/spaces](https://huggingface.co/spaces)

---

**Questions? Feedback?** I'd love to hear from you! Find me at [onurcopur.vercel.app](https://onurcopur.vercel.app) or connect with me on [LinkedIn](https://linkedin.com).

---

*Built with curiosity, debugged with patience, deployed with coffee.* ☕
