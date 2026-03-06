# OpusClaw

> Personal AI assistant with persistent memory, multi-channel support, and tool use.

Based on ["Building OpenClaw from Scratch"](https://x.com/naderdabit) by Nader Dabit.

## Quick Start

### Phase 1: Sessions + Personality ✅

```bash
# Install dependencies
pip install -r requirements.txt

# Configure
cp .env.example .env
# Edit .env with your TELEGRAM_TOKEN and ANTHROPIC_KEY

# Run
python main.py
```

Send a message on Telegram:
```
You: My name is Alex
Bot: Nice to meet you, Alex!

[hours later or after restart]

You: What's my name?
Bot: Your name is Alex!
```

## Roadmap

- [x] **Phase 1:** Sessions + SOUL.md personality ✅ 2026-03-06
- [x] **Phase 2:** Tools + Permissions ✅ 2026-03-06
- [ ] **Phase 3:** Context compaction (handle long conversations)
- [ ] **Phase 4:** Gateway pattern (multiple channels)
- [ ] **Phase 5:** Command queue (concurrent message handling)
- [ ] **Phase 6:** Heartbeats (scheduled tasks)
- [ ] **Phase 7:** Multi-agent routing

See [ARCHITECTURE.md](./ARCHITECTURE.md) for full design.

## Directory Structure

```
opusclaw/
├── main.py              # Entry point
├── agents/
│   └── main/SOUL.md     # Agent personality
├── sessions/            # Conversation history (JSONL)
├── src/
│   ├── sessions.py      # Session management
│   └── agent.py         # Agent loop
└── .env                 # Configuration
```

## What Makes This Different?

| Feature | Chatbots | OpusClaw |
|---------|----------|----------|
| Memory | Stateless | Persistent sessions |
| Personality | Generic | SOUL.md defines behavior |
| Action | Only talks | Tools to act on your behalf |
| Channels | One app | WhatsApp, Telegram, Discord, etc. |
| Automation | You must ask | Wake up on schedule (heartbeats) |
| Hosting | Their servers | Your hardware, your control |

---

*Building in public. Phase 1 complete 2026-03-06.*
