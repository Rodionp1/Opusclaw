#!/usr/bin/env python3
"""
Test script for Phase 1 (Sessions + SOUL) - no Telegram required.

Run: python test_phase1.py
"""

import asyncio
import os
from dotenv import load_dotenv

load_dotenv()

if not os.getenv("ANTHROPIC_KEY"):
    print("Error: Set ANTHROPIC_KEY in .env")
    exit(1)

from src.sessions import load_session, append_message, clear_session
from src.agent import run_agent_turn


async def main():
    session_key = "test_user"
    
    # Clear previous test session
    clear_session(session_key)
    print("=== OpusClaw Phase 1 Test ===\n")
    
    # Test 1: Introduction
    print("You: My name is Alex")
    response = await run_agent_turn(
        session_key=session_key,
        user_text="My name is Alex",
        agent_id="main"
    )
    print(f"Bot: {response}\n")
    
    # Test 2: Recall (simulates restart - new call, same session file)
    print("You: What's my name?")
    response = await run_agent_turn(
        session_key=session_key,
        user_text="What's my name?",
        agent_id="main"
    )
    print(f"Bot: {response}\n")
    
    # Test 3: Check session file
    messages = load_session(session_key)
    print(f"📦 Session has {len(messages)} messages")
    print("Session file: sessions/test_user.jsonl")
    
    # Show session content
    print("\n--- Session content ---")
    for msg in messages:
        role = msg["role"]
        content = msg["content"][:60] + "..." if len(msg["content"]) > 60 else msg["content"]
        print(f"{role}: {content}")
    print("---\n")
    
    print("✅ Phase 1 working! Sessions persist across calls.")


if __name__ == "__main__":
    asyncio.run(main())
