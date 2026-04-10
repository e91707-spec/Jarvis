import asyncio
import sys
import os
from browser_use import Agent, BrowserProfile
from browser_use.llm import ChatOllama
import re

llm = ChatOllama(model="nous-hermes2:10.7b")

WORKSPACE = "C:\\container\\workspace"

SYSTEM_PROMPT = """You are a helpful AI assistant. You can chat, browse the web, and access files ONLY in C:\\container\\workspace.

STRICT RULES:
1. Maximum 5 page visits per task
2. If you have the answer, return it immediately
3. NEVER access files outside the workspace folder
4. Provide concise but complete reports
5. Only browse the web if explicitly requested (search, visit, open website, etc.)
6. Otherwise, respond as a helpful chat assistant"""

def read_file(filename):
    path = os.path.join(WORKSPACE, filename)
    if not os.path.exists(path):
        return f"File {filename} not found in workspace"
    with open(path, "r") as f:
        return f.read()

def write_file(filename, content):
    path = os.path.join(WORKSPACE, filename)
    with open(path, "w") as f:
        f.write(content)
    return f"File {filename} saved to workspace"

def list_files():
    files = os.listdir(WORKSPACE)
    return "\n".join(files) if files else "Workspace is empty"

def is_web_request(task):
    """Check if task requires web browsing"""
    web_keywords = [
        'search', 'browse', 'visit', 'open', 'website', 'google', 'find online',
        'look up', 'check online', 'web', 'internet', 'url', 'link', 'download',
        'wikipedia', 'youtube', 'reddit', 'twitter', 'facebook', 'news'
    ]
    task_lower = task.lower()
    return any(keyword in task_lower for keyword in web_keywords)

async def chat_response(task):
    """Get LLM response without browser"""
    try:
        # Simple LLM call for chat responses
        messages = [
            {"role": "system", "content": SYSTEM_PROMPT},
            {"role": "user", "content": task}
        ]
        
        # For now, return a simple response
        # In a full implementation, you'd use the LLM directly
        response = f"I understand you want to: {task}\n\nThis is a chat-only response. If you need me to browse the web, please include words like 'search', 'visit', or 'open website'.\n\nI can also help with file operations in your workspace. Try 'list files', 'read filename', or 'write filename content'."
        return response
    except Exception as e:
        return f"Error in chat response: {e}"

async def run(task: str):
    # Handle file commands directly without the browser
    task_lower = task.lower()

    if "list files" in task_lower or "what's in the workspace" in task_lower:
        print(list_files())
        return

    if task_lower.startswith("read "):
        filename = task.split(" ", 1)[1].strip()
        print(read_file(filename))
        return

    if task_lower.startswith("write "):
        parts = task.split(" ", 2)
        if len(parts) >= 3:
            filename = parts[1].strip()
            content = parts[2].strip()
            print(write_file(filename, content))
            return

    if task_lower.startswith("save "):
        parts = task.split(" to ", 1)
        if len(parts) == 2:
            content = parts[0].replace("save ", "", 1).strip()
            filename = parts[1].strip()
            print(write_file(filename, content))
            return

    # Check if this is a web request
    if is_web_request(task):
        # Web task - use browser agent
        profile = BrowserProfile(
            headless=False,
            browser_type="camoufox"
        )
        agent = Agent(
            task=task,
            llm=llm,
            browser_profile=profile,
            system_prompt_override=SYSTEM_PROMPT,
            max_actions_per_step=3,
            use_vision=True,
        )
        result = await agent.run(max_steps=10)
        print(result)
    else:
        # Chat-only task
        response = await chat_response(task)
        print(response)

if len(sys.argv) > 1:
    task = sys.argv[1]
    model = "nous-hermes2:10.7b"
else:
    print("No task provided. Please use the UI.")
    exit()

asyncio.run(run(task))