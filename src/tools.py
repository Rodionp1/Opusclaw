"""
Tool definitions and execution with permission controls.

Tools available to the agent:
- run_command: Execute shell commands (with safety checks)
- read_file: Read files from filesystem
- write_file: Write content to files
- save_memory: Save to long-term memory
- memory_search: Search long-term memory
"""

import json
import os
import re
import subprocess
from pathlib import Path
from typing import Any

# Paths
WORKSPACE = Path(__file__).parent.parent
MEMORY_DIR = WORKSPACE / "memory"
APPROVALS_FILE = WORKSPACE / "exec-approvals.json"

# Safety configuration
SAFE_COMMANDS = {
    "ls", "cat", "head", "tail", "wc", "date", "whoami", "pwd",
    "echo", "which", "git", "python3", "python", "node", "npm",
    "pip3", "pip", "find", "grep", "uname", "uptime", "free", "df"
}

DANGEROUS_PATTERNS = [
    r"\brm\s",           # rm with space (deletion)
    r"\brm$",            # rm at end
    r"\bsudo\b",         # sudo
    r"\bchmod\b",        # chmod
    r"\bchown\b",        # chown
    r"\bcurl.*\|\s*.*sh",  # curl pipe to shell
    r"\bwget.*\|\s*.*sh",  # wget pipe to shell
    r">\s*/dev/sd",      # write to disk
    r"\bmkfs\b",         # format filesystem
    r"\bdd\b",           # dd command
]

# Tool definitions (Anthropic tool use schema)
TOOLS = [
    {
        "name": "run_command",
        "description": "Run a shell command on the user's computer. Use for checking files, running programs, git operations, etc.",
        "input_schema": {
            "type": "object",
            "properties": {
                "command": {
                    "type": "string",
                    "description": "The shell command to run"
                }
            },
            "required": ["command"]
        }
    },
    {
        "name": "read_file",
        "description": "Read the contents of a file from the filesystem.",
        "input_schema": {
            "type": "object",
            "properties": {
                "path": {
                    "type": "string",
                    "description": "Path to the file (relative to workspace or absolute)"
                }
            },
            "required": ["path"]
        }
    },
    {
        "name": "write_file",
        "description": "Write content to a file. Creates parent directories if needed.",
        "input_schema": {
            "type": "object",
            "properties": {
                "path": {
                    "type": "string",
                    "description": "Path to the file (relative to workspace or absolute)"
                },
                "content": {
                    "type": "string",
                    "description": "Content to write to the file"
                }
            },
            "required": ["path", "content"]
        }
    },
    {
        "name": "save_memory",
        "description": "Save important information to long-term memory. Use for user preferences, project details, key facts that should persist across sessions.",
        "input_schema": {
            "type": "object",
            "properties": {
                "key": {
                    "type": "string",
                    "description": "Short label for the memory (e.g., 'user-preferences', 'project-notes')"
                },
                "content": {
                    "type": "string",
                    "description": "The information to remember"
                }
            },
            "required": ["key", "content"]
        }
    },
    {
        "name": "memory_search",
        "description": "Search long-term memory for relevant information. Use at the start of conversations to recall context from previous sessions.",
        "input_schema": {
            "type": "object",
            "properties": {
                "query": {
                    "type": "string",
                    "description": "What to search for (keywords)"
                }
            },
            "required": ["query"]
        }
    },
]


def load_approvals() -> dict:
    """Load approved/denied commands from disk."""
    if APPROVALS_FILE.exists():
        with open(APPROVALS_FILE, "r") as f:
            return json.load(f)
    return {"allowed": [], "denied": []}


def save_approval(command: str, approved: bool):
    """Save a command approval decision."""
    approvals = load_approvals()
    key = "allowed" if approved else "denied"
    if command not in approvals[key]:
        approvals[key].append(command)
    
    APPROVALS_FILE.parent.mkdir(exist_ok=True)
    with open(APPROVALS_FILE, "w") as f:
        json.dump(approvals, f, indent=2)


def check_command_safety(command: str) -> str:
    """
    Check if a command is safe to run.
    
    Returns: 'safe', 'approved', or 'needs_approval'
    """
    # Extract base command
    parts = command.strip().split()
    base_cmd = parts[0] if parts else ""
    
    # Check safe commands
    if base_cmd in SAFE_COMMANDS:
        return "safe"
    
    # Check if previously approved
    approvals = load_approvals()
    if command in approvals["allowed"]:
        return "approved"
    
    # Check dangerous patterns
    for pattern in DANGEROUS_PATTERNS:
        if re.search(pattern, command, re.IGNORECASE):
            return "needs_approval"
    
    # Unknown commands need approval
    return "needs_approval"


def execute_tool(name: str, tool_input: dict) -> str:
    """
    Execute a tool and return the result.
    
    This is a synchronous version for testing.
    For production, you might want async execution.
    """
    if name == "run_command":
        cmd = tool_input["command"]
        safety = check_command_safety(cmd)
        
        if safety == "needs_approval":
            return f"Permission denied. Command '{cmd}' requires approval."
        
        try:
            result = subprocess.run(
                cmd,
                shell=True,
                capture_output=True,
                text=True,
                timeout=30,
                cwd=str(WORKSPACE)
            )
            output = result.stdout + result.stderr
            return output if output else "(command completed successfully, no output)"
        except subprocess.TimeoutExpired:
            return "Command timed out after 30 seconds"
        except Exception as e:
            return f"Error executing command: {e}"
    
    elif name == "read_file":
        path = tool_input["path"]
        # Resolve relative paths to workspace
        if not os.path.isabs(path):
            path = str(WORKSPACE / path)
        
        try:
            with open(path, "r") as f:
                content = f.read()
            # Truncate very long files
            if len(content) > 10000:
                return content[:10000] + "\n...(truncated)"
            return content
        except FileNotFoundError:
            return f"File not found: {path}"
        except Exception as e:
            return f"Error reading file: {e}"
    
    elif name == "write_file":
        path = tool_input["path"]
        content = tool_input["content"]
        
        # Resolve relative paths to workspace
        if not os.path.isabs(path):
            path = str(WORKSPACE / path)
        
        try:
            path_obj = Path(path)
            path_obj.parent.mkdir(parents=True, exist_ok=True)
            with open(path, "w") as f:
                f.write(content)
            return f"Successfully wrote to {path}"
        except Exception as e:
            return f"Error writing file: {e}"
    
    elif name == "save_memory":
        key = tool_input["key"]
        content = tool_input["content"]
        
        MEMORY_DIR.mkdir(exist_ok=True)
        filepath = MEMORY_DIR / f"{key}.md"
        
        try:
            with open(filepath, "w") as f:
                f.write(content)
            return f"Saved to memory: {key}"
        except Exception as e:
            return f"Error saving memory: {e}"
    
    elif name == "memory_search":
        query = tool_input["query"].lower()
        results = []
        
        if not MEMORY_DIR.exists():
            return "No memories found."
        
        for fname in MEMORY_DIR.glob("*.md"):
            with open(fname, "r") as f:
                content = f.read()
            
            # Simple keyword matching
            query_words = query.split()
            if any(word in content.lower() for word in query_words):
                results.append(f"--- {fname.name} ---\n{content}")
        
        if results:
            return "\n\n".join(results)
        return "No matching memories found."
    
    else:
        return f"Unknown tool: {name}"


def get_tools_schema() -> list:
    """Return the tool schema for API calls."""
    return TOOLS
