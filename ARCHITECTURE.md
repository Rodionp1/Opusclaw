# OpusClaw Architecture

Based on "Building OpenClaw from Scratch" by Nader Dabit

## Core Principles

1. **Progressive Enhancement** — Start minimal, add features iteratively
2. **File-Based Persistence** — Sessions, memory, approvals all stored as files (crash-safe, inspectable)
3. **JSONL for Sessions** — Append-only, one message per line, easy to compact
4. **Decoupled Channels** — Gateway pattern: agent logic separate from channel adapters
5. **Per-Session Locking** — Prevent race conditions without blocking unrelated sessions

## Directory Structure

```
opusclaw/
├── main.py                 # Entry point (CLI or daemon)
├── config.json             # Channels, agents, settings
├── agents/
│   ├── main/
│   │   └── SOUL.md         # Personality for main agent
│   └── researcher/
│       └── SOUL.md         # Personality for researcher agent
├── sessions/               # JSONL session files
│   ├── agent_main_user123.jsonl
│   ├── agent_researcher_user123.jsonl
│   └── cron_morning-brief.jsonl
├── memory/                 # Long-term memory files
│   ├── user-preferences.md
│   └── project-notes.md
├── src/
│   ├── __init__.py
│   ├── agent.py            # Core agent loop + tool execution
│   ├── sessions.py         # Session management + compaction
│   ├── memory.py           # Memory save/search
│   ├── tools.py            # Tool definitions + exec
│   ├── gateway.py          # Channel management
│   ├── channels/
│   │   ├── __init__.py
│   │   ├── telegram.py     # Telegram adapter
│   │   └── http.py         # HTTP API adapter
│   └── scheduler.py        # Heartbeats/cron
└── .env                    # Tokens (TELEGRAM_TOKEN, ANTHROPIC_KEY)
```

## Implementation Phases

### Phase 1: Core Agent Loop (MVP) ✅ COMPLETE 2026-03-06

**Goal:** Agent that remembers within a session and has a personality.

**Files created:**
- `src/sessions.py` — Load/save JSONL sessions
- `src/agent.py` — Agent loop with SOUL.md injection
- `agents/main/SOUL.md` — Basic personality

**What works:**
```
You: My name is Alex
Bot: Nice to meet you, Alex!

[restart bot]

You: What's my name?
Bot: Your name is Alex!
```

**Tested:** 2026-03-06 ✅

---

### Phase 2: Tools + Permissions ✅ COMPLETE 2026-03-06

**Goal:** Agent can act, not just talk.

**Files created:**
- `src/tools.py` — Tool definitions + execution + safety
- `exec-approvals.json` — Persisted allowlist (created on first approval)

**Tools implemented:**
1. `run_command` — Shell execution with safety checks
2. `read_file` — Read from filesystem
3. `write_file` — Write to filesystem
4. `save_memory` — Save to long-term memory
5. `memory_search` — Search long-term memory

**Safety:**
- SAFE_COMMANDS allowlist (ls, cat, pwd, git, etc.)
- DANGEROUS_PATTERNS blocklist (rm, sudo, chmod, curl|sh)
- Unknown commands require approval

**What works:**
```
You: List files
Bot: [runs ls -la]
     Here's what's in your workspace...

You: Create hello.txt with "Hello World"
Bot: [writes file]
     Done!

You: Remember my favorite color is blue
Bot: [saves to memory]
     Got it — saved.

You: What's my favorite color?
Bot: [searches memory]
     Your favorite color is blue.
```

**Tested:** 2026-03-06 ✅

---

### Phase 3: Context Compaction

**Goal:** Handle long conversations without hitting token limits.

**Files to modify:**
- `src/sessions.py` — Add `compact_session()` function

**How it works:**
- Estimate tokens (~4 chars per token)
- When >100k tokens: split session, summarize old half, keep recent half
- Summary includes: user facts, decisions, open tasks

---

### Phase 4: Gateway Pattern

**Goal:** Multiple channels, same agent, shared sessions.

**Files to create:**
- `src/gateway.py` — Channel router
- `src/channels/__init__.py` — Channel interface
- `src/channels/telegram.py` — Telegram adapter
- `src/channels/http.py` — HTTP API (Flask/FastAPI)

**Key insight:** `run_agent_turn()` takes messages, returns text. Channel doesn't matter.

---

### Phase 5: Command Queue (Locking)

**Goal:** Handle concurrent messages safely.

**Files to modify:**
- `src/sessions.py` — Add per-session locks

**How it works:**
- `session_locks = defaultdict(threading.Lock)`
- Wrap session operations in `with session_locks[session_key]:`
- Same user queues up; different users run parallel

---

### Phase 6: Heartbeats (Cron)

**Goal:** Agent wakes up on schedule.

**Files to create:**
- `src/scheduler.py` — Cron job management

**How it works:**
- Use `schedule` library or cron expressions
- Each heartbeat has isolated session key (`cron:morning-brief`)
- Doesn't pollute main conversation history

---

### Phase 7: Multi-Agent Routing

**Goal:** Different personalities for different tasks.

**Files to create:**
- `agents/researcher/SOUL.md` — Research specialist personality
- routing logic in `src/agent.py`

**How it works:**
- `/research <query>` → route to researcher agent
- Each agent has separate session files
- All agents share `memory/` directory

---

## Configuration Schema

```json
{
  "anthropic_key": "...",
  "model": "claude-sonnet-4-5-20250929",
  "channels": {
    "telegram": {
      "token": "...",
      "enabled": true
    },
    "http": {
      "port": 5000,
      "enabled": true
    }
  },
  "agents": ["main", "researcher"],
  "heartbeats": [
    {
      "name": "morning-brief",
      "schedule": "07:30",
      "prompt": "Good morning! Check today's date and give a motivational quote."
    }
  ],
  "session_compaction_threshold": 100000
}
```

---

## Tool Schema (Anthropic Tool Use)

```python
TOOLS = [
    {
        "name": "run_command",
        "description": "Run a shell command on the user's computer",
        "input_schema": {
            "type": "object",
            "properties": {
                "command": {"type": "string", "description": "The command to run"}
            },
            "required": ["command"]
        }
    },
    # ... more tools
]
```

---

## Session File Format (JSONL)

```jsonl
{"role": "user", "content": "My name is Alex"}
{"role": "assistant", "content": "Nice to meet you, Alex!"}
{"role": "user", "content": "What's my name?"}
{"role": "assistant", "content": "Your name is Alex!"}
```

**Why JSONL?**
- Append-only (crash-safe)
- Each line is valid JSON (easy to parse incrementally)
- Easy to truncate/compact

---

## Progress Summary

| Phase | Feature | Status | Date |
|-------|---------|--------|------|
| 1 | Sessions + SOUL | ✅ Complete | 2026-03-06 |
| 2 | Tools + Permissions | ✅ Complete | 2026-03-06 |
| 3 | Context Compaction | ⏳ Pending | — |
| 4 | Gateway Pattern | ⏳ Pending | — |
| 5 | Command Queue | ⏳ Pending | — |
| 6 | Heartbeats | ⏳ Pending | — |
| 7 | Multi-Agent | ⏳ Pending | — |

*Created: 2026-03-06 | Updated: 2026-03-06*
