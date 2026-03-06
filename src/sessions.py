"""
Session management with JSONL persistence.

Each session is a file: sessions/<session_key>.jsonl
Format: one JSON message per line (append-only, crash-safe)
"""

import json
import os
from pathlib import Path

SESSIONS_DIR = Path("./sessions")


def ensure_sessions_dir():
    """Create sessions directory if it doesn't exist."""
    SESSIONS_DIR.mkdir(exist_ok=True)


def get_session_path(session_key: str) -> Path:
    """Convert session key to safe filename."""
    # Replace problematic chars for filenames
    safe_key = session_key.replace(":", "_").replace("/", "_")
    return SESSIONS_DIR / f"{safe_key}.jsonl"


def load_session(session_key: str) -> list:
    """Load conversation history from disk."""
    ensure_sessions_dir()
    path = get_session_path(session_key)
    messages = []
    
    if path.exists():
        with open(path, "r") as f:
            for line in f:
                if line.strip():
                    try:
                        messages.append(json.loads(line))
                    except json.JSONDecodeError:
                        # Skip corrupted lines
                        continue
    
    return messages


def append_message(session_key: str, message: dict):
    """Append a single message to the session file (append-only)."""
    ensure_sessions_dir()
    path = get_session_path(session_key)
    
    with open(path, "a") as f:
        f.write(json.dumps(message) + "\n")


def save_session(session_key: str, messages: list):
    """Overwrite the session file with full message list."""
    ensure_sessions_dir()
    path = get_session_path(session_key)
    
    with open(path, "w") as f:
        for msg in messages:
            f.write(json.dumps(msg) + "\n")


def clear_session(session_key: str):
    """Delete a session file (for /new command)."""
    path = get_session_path(session_key)
    if path.exists():
        path.unlink()
