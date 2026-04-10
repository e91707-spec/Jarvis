import sys
import os
import json
import httpx
import asyncio
import re
import fnmatch
import subprocess
import glob
import platform
from pathlib import Path
from groq_client import groq_client

sys.stdout.reconfigure(encoding='utf-8')

WORKSPACE = "C:\\container\\workspace"
OLLAMA_URL = "http://localhost:11434/api/chat"
MODEL = "nous-hermes2:10.7b"

def create_subprocess(*args, **kwargs):
    """Cross-platform subprocess creation"""
    subprocess_kwargs = kwargs.copy()
    
    # Add creationflags only on Windows
    if platform.system() == "Windows":
        subprocess_kwargs.setdefault("creationflags", 0x08000000)
    
    return subprocess.Popen(*args, **subprocess_kwargs)

# Detect all available drives on Windows
def get_all_drives():
    """Detect all available drives on the system"""
    drives = []
    import string
    for letter in string.ascii_uppercase:
        drive = f"{letter}:\\"
        if os.path.exists(drive):
            drives.append(drive)
    return drives

# Common user directories to search
USER_DIRS = [
    "C:\\Users", 
    "C:\\Documents and Settings",
    "C:\\Program Files",
    "C:\\Program Files (x86)",
    "C:\\ProgramData"
]

SYSTEM_PROMPT = """You are an intelligent routing assistant that determines which agent should handle a user's request.

You respond with ONLY a single JSON object, nothing else.

Available agents:
{ "agent": "file_agent", "reason": "for workspace file operations" }
{ "agent": "admin_agent", "reason": "for system-wide file searches" }
{ "agent": "browser_agent", "reason": "for web searches" }
{ "agent": "chat_agent", "reason": "for general conversation and questions" }
{ "agent": "unknown", "reason": "if request is unclear" }

FILE SEARCH KEYWORDS (use admin_agent):
- find file, find files, search for file, search for files
- locate file, locate files, search files, locate
- find on computer, find on system, search system
- search directory, find directory, search folder, find folder
- look for file, look for files, find document, find documents
- search for log files, find config files, locate executable
- find .txt files, find .py files, find .log files, etc.
- search my files, find my files, locate my files

WORKSPACE KEYWORDS (use file_agent):
- list files, workspace, read, write, save
- create file, open file, delete file, edit file
- what files, show files, workspace files

WEB SEARCH KEYWORDS (use browser_agent):
- search the web, search online, search internet
- google search, web search, internet search
- look up online, find online, search for information
- research, look up, find information about
- search for tutorials, search for documentation

CHAT KEYWORDS (use chat_agent):
- hello, hi, how are you, what's up
- help, assist, explain, tell me about
- what is, how to, why, when, where
- can you, could you, would you
- general questions, conversation, chat
- advice, opinion, recommend
- explain concept, help me understand

RULES:
1. Check for FILE SEARCH keywords first - if present, use admin_agent
2. Check for WORKSPACE keywords next - if present, use file_agent  
3. Check for CHAT keywords next - if present, use chat_agent
4. Check for WEB SEARCH keywords last - if present, use browser_agent
5. If no keywords match, use chat_agent as default for general conversation
6. Always provide a brief reason for your choice
7. Be decisive - pick one agent only"""

def request_execution_confirmation(task, filepath):
    """Request user confirmation for file execution via verify_agent.py"""
    try:
        process = subprocess.run(
            ["python", "verify_agent.py", "confirm_execution", filepath, task],
            text=True,
            capture_output=True,
            cwd="C:\\container"
        )
        if process.returncode == 2:
            # Confirmation is pending, not yet answered
            print(process.stdout.strip(), flush=True)
            return "pending"
        if process.returncode == 0:
            return True
        print(process.stdout.strip(), flush=True)
        return False
    except Exception as e:
        print(f"Error requesting execution confirmation: {str(e)}", flush=True)
        return False

def handle_execution_confirmation_response(response):
    """Handle user's execution confirmation response using verify_agent.py"""
    try:
        process = subprocess.run(
            ["python", "verify_agent.py", "execution_response", response],
            text=True,
            capture_output=True,
            cwd="C:\\container"
        )
        
        if process.returncode == 0:
            # Extract the filepath from output
            for line in process.stdout.splitlines():
                if line.strip().startswith("EXECUTION_FILE:"):
                    return line.strip().replace("EXECUTION_FILE:", "", 1).strip()
        return None
    except Exception as e:
        print(f"Error handling execution confirmation response: {str(e)}", flush=True)
        return None

def search_all_drives(pattern):
    """Search across all available drives for files with timeout"""
    result = [None]
    exception = [None]

    def search_worker():
        try:
            result[0] = _search_all_drives_impl(pattern)
        except Exception as e:
            exception[0] = e
            result[0] = f"Search failed: {str(e)}"

    thread = threading.Thread(target=search_worker, daemon=True)
    thread.start()
    thread.join(timeout=30)  # 30 second timeout

    if thread.is_alive():
        return "Search timed out after 30 seconds. Try a more specific search pattern."
    elif exception[0]:
        return f"Search error: {str(exception[0])}"
    else:
        return result[0]

def _search_all_drives_impl(pattern):
    """Search across all available drives for files"""
    results = []
    drives = get_all_drives()
    
    print(f"Searching {len(drives)} drives: {', '.join(drives)}", flush=True)
    
    for drive in drives:
        if os.path.exists(drive):
            found = []
            try:
                for root, dirs, files in os.walk(drive, topdown=True, onerror=lambda e: None):
                    rel_root = os.path.relpath(root, drive)
                    for filename in files:
                        filepath = os.path.join(root, filename)
                        rel_path = os.path.join(rel_root, filename) if rel_root != '.' else filename
                        if fnmatch.fnmatch(filename, pattern) or fnmatch.fnmatch(rel_path, pattern):
                            found.append(filepath)
                    if len(found) >= 100:
                        break

                if len(found) > 100:
                    results.append(f"Found 100+ files on {drive} (showing first 100):")
                    found = found[:100]
                else:
                    results.append(f"Found {len(found)} file(s) on {drive}:")

                for file in sorted(found):
                    results.append(f"  {file}")
                    
            except Exception as e:
                results.append(f"Error searching {drive}: {str(e)}")
    
    return "\n".join(results) if results else "No files found on any drives."

def search_user_directories(pattern):
    """Search in user directories only"""
    results = []
    
    for user_dir in USER_DIRS:
        if os.path.exists(user_dir):
            try:
                search_pattern = os.path.join(user_dir, pattern)
                files = glob.glob(search_pattern, recursive=True)
                
                if files:
                    results.append(f"Found {len(files)} file(s) in {user_dir}:")
                    for file in sorted(files):
                        results.append(f"  {file}")
                        
            except Exception as e:
                results.append(f"Error searching {user_dir}: {str(e)}")
    
    return "\n".join(results) if results else "No files found in user directories."

async def route_request(task):
    """Determine which agent should handle the request"""
    messages = [
        {"role": "system", "content": SYSTEM_PROMPT},
        {"role": "user", "content": task}
    ]
    
    print("Analyzing request...", flush=True)
    
    async def ask_ollama(messages):
        print("Thinking...", flush=True)
        try:
            response = await groq_client.chat_completion(messages, json_mode=True)
            return response
        except Exception as e:
            print(f"Error using Groq API: {str(e)}", flush=True)
            # Fallback to simple response
            return "I'm having trouble connecting to the AI service. Please try again."

    response = await ask_ollama(messages)
    return response

async def run_admin_agent(task):
    """Handle system-wide file searches by launching admin_agent.py subprocess"""
    print("Admin Agent: Handling file search request", flush=True)

    # Launch admin_agent.py as subprocess
    try:
        process = create_subprocess(
            ["python", "-u", "admin_agent.py", task],
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,
            encoding="utf-8",
            bufsize=1,
            cwd="C:\\container"
        )
        
        output_lines = []
        for line in process.stdout:
            line = line.strip()
            if line:
                print(line, flush=True)
                output_lines.append(line)
        
        process.wait()
        
        # Check if the last output indicates a confirmation is needed
        if output_lines and output_lines[-1].startswith("CONFIRM_EXECUTION:"):
            filepath = output_lines[-1].replace("CONFIRM_EXECUTION:", "", 1)
            print(f"Execution confirmation needed for: {filepath}", flush=True)
            # Trigger confirmation system
            confirmation_result = request_execution_confirmation(task, filepath)
            if confirmation_result == "pending":
                print("Execution request pending confirmation. Please reply 'yes' or 'no'.", flush=True)
                return
            elif confirmation_result:
                print("Confirmation received. Executing file...", flush=True)
                try:
                    create_subprocess([str(filepath)], cwd=str(Path(filepath).parent))
                    print(f"Successfully executed '{Path(filepath).name}'")
                except Exception as e:
                    print(f"Error executing file: {str(e)}")
            else:
                print("Execution cancelled by user.", flush=True)
        
    except Exception as e:
        print(f"Error running admin agent: {str(e)}", flush=True)

async def run_admin_agent_with_confirmation(task, pattern):
    """Handle the confirmed full computer search"""
    print("Confirmation received. Searching entire computer...", flush=True)
    results = search_all_drives(pattern)
    print(results, flush=True)

async def run_file_agent(task):
    """Handle workspace file operations"""
    print("File Agent: Handling workspace operation", flush=True)
    
    # Launch file_agent.py
    try:
        process = create_subprocess(
            ["python", "-u", "file_agent.py", task],
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,
            encoding="utf-8",
            bufsize=1,
            cwd="C:\\container"
        )
        for line in process.stdout:
            line = line.strip()
            if line:
                print(line, flush=True)
        process.wait()
    except Exception as e:
        print(f"Error running file agent: {str(e)}", flush=True)

async def run_browser_agent(task):
    """Handle web searches"""
    print("Browser Agent: Handling web search", flush=True)
    
    # Launch browser_agent.py
    try:
        process = create_subprocess(
            ["python", "-u", "ai_browser_native.py", task],
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,
            encoding="utf-8",
            bufsize=1,
            cwd="C:\\container"
        )
        for line in process.stdout:
            line = line.strip()
            if line:
                print(line, flush=True)
        process.wait()
    except Exception as e:
        print(f"Error running browser agent: {str(e)}", flush=True)

async def run_chat_agent(task):
    """Handle general conversation and questions"""
    print("Chat Agent: Handling conversation", flush=True)
    
    # Launch chat_agent.py
    try:
        process = create_subprocess(
            ["python", "-u", "chat_agent.py", task],
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,
            encoding="utf-8",
            bufsize=1,
            cwd="C:\\container"
        )
        for line in process.stdout:
            line = line.strip()
            if line:
                print(line, flush=True)
        process.wait()
    except Exception as e:
        print(f"Error running chat agent: {str(e)}", flush=True)

def check_confirmation_context():
    """Check if there's an active confirmation waiting for response"""
    context_file = "C:\\container\\confirmation_context.json"
    if os.path.exists(context_file):
        try:
            with open(context_file, 'r') as f:
                context = json.load(f)
                return True, context
        except:
            return False, None
    return False, None

async def main():
    if len(sys.argv) < 2:
        print("No task provided.", flush=True)
        return
    
    task = " ".join(sys.argv[1:])
    task_lower = task.lower()
    print(f"Processing: {task}", flush=True)
    
    try:
        # First check if this is a confirmation response
        has_context, context = check_confirmation_context()
        if has_context:
            if context.get('type') == 'execution':
                print("Detected execution confirmation response, processing...", flush=True)
                filepath = handle_execution_confirmation_response(task_lower)
                if filepath:
                    print("Confirmation received. Executing file...", flush=True)
                    try:
                        create_subprocess([str(filepath)], cwd=str(Path(filepath).parent))
                        print(f"Successfully executed '{Path(filepath).name}'")
                    except Exception as e:
                        print(f"Error executing file: {str(e)}")
                else:
                    print("Execution cancelled by user.", flush=True)
            else:
                print("Detected confirmation response, routing to admin_agent", flush=True)
                await run_admin_agent(task)
            return
        
        # Check for FILE SEARCH keywords first - if present, use admin_agent
        task_lower = task.lower()
        file_search_keywords = [
            "find file", "search for file", "locate file", "find the file", "search file",
            "find *.txt", "find *.py", "find *.log", "find *.exe", "find *.doc", "find *.pdf",
            "find and", "locate and", "search and",
            "search entire computer", "search all drives", "search system", "system search",
            "computer search", "full search", "comprehensive search", "find anywhere",
            "search everywhere", "global search", "find on computer", "locate on system"
        ]
        
        if any(keyword in task_lower for keyword in file_search_keywords):
            print("Detected file search keywords, routing to admin_agent", flush=True)
            await run_admin_agent(task)
            return
        
        # Route the request normally using LLM
        routing_decision = await route_request(task)
        
        try:
            decision = json.loads(routing_decision)
            agent = decision.get("agent", "browser_agent")
            reason = decision.get("reason", "No reason provided")
            print(f"Routing to {agent} ({reason})", flush=True)
        except json.JSONDecodeError:
            # Fallback to browser agent if JSON parsing fails
            agent = "browser_agent"
            print(f"Routing to {agent} (fallback)", flush=True)
        
        # Execute the appropriate agent
        if agent == "admin_agent":
            await run_admin_agent(task)
        elif agent == "file_agent":
            await run_file_agent(task)
        elif agent == "browser_agent":
            await run_browser_agent(task)
        elif agent == "chat_agent":
            await run_chat_agent(task)
        else:
            print("Unknown request type. Using chat agent.", flush=True)
            await run_chat_agent(task)
            
    except Exception as e:
        print(f"Error in brains.py: {str(e)}", flush=True)

if __name__ == "__main__":
    asyncio.run(main())
