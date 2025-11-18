# Quick Start Guide

## 🚀 Get Started in 5 Minutes

### 1. Install Dependencies

```bash
cd story-crafter-adk
uv sync
```

### 2. Set Your API Key

```bash
export GOOGLE_API_KEY="your-api-key-here"
```

Or copy `.env.example` to `.env` and add your key:

```bash
cp .env.example .env
# Edit .env and add your key
```

### 3. Run an Example

**Option A: Use the example script**

```bash
uv run python example.py
```

**Option B: Use ADK CLI directly**

```bash
uv run adk run orchestrator/story_orchestrator --user_message "Create a 5-minute bedtime story about a brave mermaid for an 8-year-old"
```

**Option C: Test a single agent**

```bash
uv run adk run agents/user_intent --user_message "I want an exciting space adventure for a 10-year-old"
```

### 4. Use in Your Code

```python
import asyncio
from orchestrator.story_orchestrator.agent import story_orchestrator, runtime

async def generate():
    result = await runtime.run_agent(
        story_orchestrator,
        "Create a story about dragons for a 10-year-old"
    )
    print(result.output_text)

asyncio.run(generate())
```

## 📁 Project Structure

```
story-crafter-adk/
├── agents/              # Individual story agents
├── models/              # Pydantic data models
├── orchestrator/        # Multi-agent coordination
├── example.py          # Example usage script
└── README.md           # Full documentation
```

## 🎨 Available Agents

| Agent | Purpose | Run Command |
|-------|---------|-------------|
| User Intent | Extract story requirements | `uv run adk run agents/user_intent` |
| Worldbuilder | Create story worlds | `uv run adk run agents/worldbuilder` |
| Character Forge | Design characters | `uv run adk run agents/character_forge` |
| Plot Architect | Structure plots | `uv run adk run agents/plot_architect` |
| Story Writer | Write narrative prose | `uv run adk run agents/story_writer` |
| Art Director | Generate illustration prompts | `uv run adk run agents/art_director` |
| **Orchestrator** | **Run all agents together** | `uv run adk run orchestrator/story_orchestrator` |

## 🐛 Troubleshooting

**"API Key not found"**
- Ensure `GOOGLE_API_KEY` is set: `echo $GOOGLE_API_KEY`
- Or check your `.env` file exists and has the key

**"Module not found"**
- Run `uv sync` to install dependencies
- Make sure you're in the project root

**Need more help?**
- See the full [README.md](README.md) for detailed documentation
- Check example.py for code samples

## 🎯 Next Steps

1. Read the full [README.md](README.md) for architecture details
2. Explore individual agents in `agents/` directory
3. Customize agent prompts for your use case
4. Build your own workflows using the agents as building blocks

---

**Built with Google Agent Development Kit (ADK)**

