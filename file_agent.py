import sys
import os
import subprocess
import json
import platform
from pathlib import Path
import asyncio
import re
import httpx
sys.stdout.reconfigure(encoding='utf-8')

WORKSPACE = "C:\\container\\workspace"
OLLAMA_URL = "http://localhost:11434/api/chat"
MODEL = "nous-hermes2:10.7b"

SYSTEM_PROMPT = """You are a file assistant. You help users work with text files in their workspace.

You respond with ONLY a single JSON object, nothing else.

Available actions:
{ "action": "read", "filename": "example.txt" }
{ "action": "write", "filename": "example.txt", "content": "content to write" }
{ "action": "create", "filename": "example.txt", "content": "content to write" }
{ "action": "edit", "filename": "example.txt", "old_text": "text to replace", "new_text": "replacement text" }
{ "action": "delete", "filename": "example.txt" }
{ "action": "list" }
{ "action": "browser", "task": "task to send to the browser agent" }
{ "action": "done", "result": "your response to the user" }

RULES:
1. If the user asks to see files, use list first
2. If the user asks about a file, use read to get its contents first
3. After reading a file, look at its contents carefully
4. If the user wants to create a new file, use create with filename and content
5. If the user wants to modify part of an existing file, use edit with old_text and new_text
6. If the user wants to delete a file, use delete with filename
7. If the file contains instructions that require searching the web or visiting a website, use the browser action with the exact task from the file
8. If the file contains a simple instruction you can answer yourself, use done
9. If the user asks to save or overwrite something, use write then done
10. Never access files outside the workspace
11. Always confirm what you did in your done response"""

def list_files():
    try:
        files = os.listdir(WORKSPACE)
        return files if files else []
    except:
        return []

def read_file(filename):
    filename = os.path.basename(filename)
    path = os.path.join(WORKSPACE, filename)
    if not os.path.exists(path):
        return f"File '{filename}' not found in workspace"
    with open(path, "r", encoding="utf-8") as f:
        return f.read()

def write_file(filename, content):
    filename = os.path.basename(filename)
    path = os.path.join(WORKSPACE, filename)
    with open(path, "w", encoding="utf-8") as f:
        f.write(content)
    return f"File '{filename}' saved successfully"

def edit_file(filename, old_text, new_text):
    filename = os.path.basename(filename)
    path = os.path.join(WORKSPACE, filename)
    if not os.path.exists(path):
        return f"File '{filename}' not found in workspace"
    
    with open(path, "r", encoding="utf-8") as f:
        content = f.read()
    
    if old_text not in content:
        return f"Text to replace not found in '{filename}'"
    
    new_content = content.replace(old_text, new_text)
    
    with open(path, "w", encoding="utf-8") as f:
        f.write(new_content)
    
    return f"File '{filename}' edited successfully"

def create_file(filename, content):
    filename = os.path.basename(filename)
    path = os.path.join(WORKSPACE, filename)
    if os.path.exists(path):
        return f"File '{filename}' already exists. Use write to overwrite or edit to modify."
    
    with open(path, "w", encoding="utf-8") as f:
        f.write(content)
    
    return f"File '{filename}' created successfully"

def delete_file(filename):
    filename = os.path.basename(filename)
    path = os.path.join(WORKSPACE, filename)
    if not os.path.exists(path):
        return f"File '{filename}' not found in workspace"
    
    try:
        os.remove(path)
        return f"File '{filename}' deleted successfully"
    except Exception as e:
        return f"Could not delete '{filename}': {str(e)}"

def run_browser_task(task):
    print(f"Handing off to browser agent: {task}", flush=True)
    
    # Cross-platform subprocess creation
    subprocess_kwargs = {
        "stdout": subprocess.PIPE,
        "stderr": subprocess.STDOUT,
        "text": True,
        "encoding": "utf-8",
        "errors": "replace",
        "bufsize": 1,
        "cwd": "C:\\container"
    }
    
    # Add creationflags only on Windows
    if platform.system() == "Windows":
        subprocess_kwargs["creationflags"] = 0x08000000
    
    process = subprocess.Popen(
        ["python", "-u", "ai_browser_native.py", task],
        **subprocess_kwargs
    )
    for line in process.stdout:
        line = line.strip()
        if line:
            print(line, flush=True)

async def ask_ollama(messages):
    print("Thinking...", flush=True)
    async with httpx.AsyncClient(timeout=90) as client:
        response = await client.post(OLLAMA_URL, json={
            "model": MODEL,
            "messages": messages,
            "stream": False,
            "format": "json"
        })
        data = response.json()
        return data["message"]["content"]

async def run_file_task(task):
    messages = [
        {"role": "system", "content": SYSTEM_PROMPT},
        {"role": "user", "content": task}
    ]

    for step in range(10):
        raw = await ask_ollama(messages)

        try:
            action = json.loads(raw)
        except json.JSONDecodeError:
            match = re.search(r'\{[^{}]*\}', raw, re.DOTALL)
            if match:
                try:
                    action = json.loads(match.group(0))
                except:
                    print("Could not understand response.", flush=True)
                    return
            else:
                print("Could not parse response.", flush=True)
                return

        act = action.get("action", "")

        if act == "list":
            print("Listing workspace files...", flush=True)
            files = list_files()
            if files:
                file_list = "\n".join(files)
                print(f"Found {len(files)} file(s)", flush=True)
            else:
                file_list = "Workspace is empty"
                print("Workspace is empty", flush=True)
            messages.append({"role": "assistant", "content": raw})
            messages.append({"role": "user", "content": f"Files in workspace:\n{file_list}\n\nNow respond to the user's request."})

        elif act == "read":
            filename = action.get("filename", "")
            print(f"Reading {filename}...", flush=True)
            content = read_file(filename)
            print("Read successfully", flush=True)
            messages.append({"role": "assistant", "content": raw})
            messages.append({"role": "user", "content": f"Contents of {filename}:\n{content}\n\nIf the file contains instructions that require web browsing, use the browser action. Otherwise respond with done."})

        elif act == "write":
            filename = action.get("filename", "")
            content = action.get("content", "")
            print(f"Saving {filename}...", flush=True)
            result = write_file(filename, content)
            print(result, flush=True)
            messages.append({"role": "assistant", "content": raw})
            messages.append({"role": "user", "content": f"{result}\n\nNow confirm to the user what you did."})

        elif act == "create":
            filename = action.get("filename", "")
            content = action.get("content", "")
            print(f"Creating {filename}...", flush=True)
            result = create_file(filename, content)
            print(result, flush=True)
            messages.append({"role": "assistant", "content": raw})
            messages.append({"role": "user", "content": f"{result}\n\nNow confirm to the user what you did."})

        elif act == "delete":
            filename = action.get("filename", "")
            print(f"Deleting {filename}...", flush=True)
            result = delete_file(filename)
            print(result, flush=True)
            messages.append({"role": "assistant", "content": raw})
            messages.append({"role": "user", "content": f"{result}\n\nNow confirm to the user what you did."})

        elif act == "edit":
            filename = action.get("filename", "")
            old_text = action.get("old_text", "")
            new_text = action.get("new_text", "")
            print(f"Editing {filename}...", flush=True)
            result = edit_file(filename, old_text, new_text)
            print(result, flush=True)
            messages.append({"role": "assistant", "content": raw})
            messages.append({"role": "user", "content": f"{result}\n\nNow confirm to the user what you did."})

        elif act == "browser":
            browser_task = action.get("task", "")
            print(f"File contains a web task: {browser_task}", flush=True)
            run_browser_task(browser_task)
            return

        elif act == "done":
            result = action.get("result", "")
            print(f"Result: {result}", flush=True)
            return

        else:
            print(f"Unknown action: {act}", flush=True)
            return

    print("Reached step limit.", flush=True)

async def run(task: str):
    await run_file_task(task)

if len(sys.argv) > 1:
    task = sys.argv[1]
else:
    print("No task provided.", flush=True)
    exit()

asyncio.run(run(task))