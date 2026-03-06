"""
Core agent loop with personality (SOUL) injection and tool execution.

The agent:
1. Loads session history
2. Injects SOUL as system prompt
3. Calls Claude with tool support
4. Executes any requested tools
5. Loops until done
"""

import os
from pathlib import Path
from typing import Optional
from anthropic import AsyncAnthropic

from .sessions import load_session, append_message, save_session
from .tools import execute_tool, get_tools_schema

# Paths
WORKSPACE = Path(__file__).parent.parent
AGENTS_DIR = WORKSPACE / "agents"

# Claude client (lazy init)
_client: Optional[AsyncAnthropic] = None


def get_client() -> AsyncAnthropic:
    """Get or create Anthropic client."""
    global _client
    if _client is None:
        api_key = os.getenv("ANTHROPIC_KEY") or os.getenv("ANTHROPIC_API_KEY")
        if not api_key:
            raise ValueError("ANTHROPIC_KEY or ANTHROPIC_API_KEY required")
        _client = AsyncAnthropic(api_key=api_key)
    return _client


def load_soul(agent_id: str) -> str:
    """Load agent personality from SOUL.md."""
    soul_path = AGENTS_DIR / agent_id / "SOUL.md"
    if not soul_path.exists():
        return "You are a helpful AI assistant."
    
    with open(soul_path, "r") as f:
        return f.read()


async def run_agent_turn(
    session_key: str,
    user_text: str,
    agent_id: str = "main",
    enable_tools: bool = True,
    max_turns: int = 20
) -> str:
    """
    Run one full agent turn (may involve multiple tool-use loops).
    
    Args:
        session_key: Unique identifier for this session
        user_text: User's message
        agent_id: Which agent to use (main, researcher, etc.)
        enable_tools: Whether to allow tool use
        max_turns: Maximum tool-use iterations
    
    Returns: Final text response to send to user
    """
    client = get_client()
    soul = load_soul(agent_id)
    model = os.getenv("CLAUDE_MODEL", "claude-sonnet-4-5-20250929")
    tools = get_tools_schema() if enable_tools else []
    
    # Load session
    messages = load_session(session_key)
    
    # Add user message
    user_msg = {"role": "user", "content": user_text}
    messages.append(user_msg)
    append_message(session_key, user_msg)
    
    # Agent loop (handle tool use iterations)
    for turn in range(max_turns):
        # Call Claude
        response = await client.messages.create(
            model=model,
            max_tokens=4096,
            system=soul,
            tools=tools,
            messages=messages
        )
        
        # Serialize response content
        content_blocks = []
        for block in response.content:
            if hasattr(block, "text"):
                content_blocks.append({"type": "text", "text": block.text})
            elif block.type == "tool_use":
                content_blocks.append({
                    "type": "tool_use",
                    "id": block.id,
                    "name": block.name,
                    "input": block.input
                })
        
        # Save assistant message
        assistant_msg = {"role": "assistant", "content": content_blocks}
        messages.append(assistant_msg)
        append_message(session_key, assistant_msg)
        
        # Check if done
        if response.stop_reason == "end_turn":
            # Extract text response
            text_parts = [b.text for b in response.content if hasattr(b, "text")]
            return "".join(text_parts)
        
        # Process tool calls
        if response.stop_reason == "tool_use":
            tool_results = []
            
            for block in response.content:
                if block.type == "tool_use":
                    print(f"  🔧 Tool: {block.name}({block.input})")
                    
                    # Execute the tool
                    result = execute_tool(block.name, block.input)
                    print(f"     → {result[:100]}...")
                    
                    tool_results.append({
                        "type": "tool_result",
                        "tool_use_id": block.id,
                        "content": result
                    })
            
            # Feed results back to Claude
            results_msg = {"role": "user", "content": tool_results}
            messages.append(results_msg)
            append_message(session_key, results_msg)
    
    return "(max turns reached)"
