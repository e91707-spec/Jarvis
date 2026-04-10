import sys
import os
import subprocess
import json
import platform
from pathlib import Path

sys.stdout.reconfigure(encoding='utf-8')

WORKSPACE = "C:\\container\\workspace"
OLLAMA_URL = "http://localhost:11434/api/chat"
MODEL = "nous-hermes2:10.7b"

SYSTEM_PROMPT = """You are Jarvis, an admin assistant that handles system-wide file searches.

You respond with ONLY a single JSON object, nothing else.

Available actions:
{ "action": "search_system", "pattern": "*.txt", "path": "C:\\" }
{ "action": "open_file", "filepath": "C:\\path\\to\\file.txt" }
{ "action": "read_file", "filepath": "C:\\path\\to\\file.txt" }
{ "action": "execute_file", "filepath": "C:\\path\\to\\program.exe" }
{ "action": "web_search", "query": "search terms" }
{ "action": "done", "result": "your response to the user" }

RULES:
1. Always use search_system for file searches - it searches all drives
2. Be specific about file patterns (*.txt, *.py, *.log, etc.)
3. For open_file: safe for text files, documents, images - opens with default application
4. For read_file: reads and displays file contents for text files only
5. For execute_file: runs executable files (.exe, .bat, etc.) - ALWAYS requires user confirmation
6. Use execute_file for games, applications, and programs that need to run
7. Use open_file for documents, images, and files you want to view/edit
8. Always provide clear results with file paths
9. Workspace is: C:\\container\\workspace
10. For multi-step requests like "find file then read file", complete each step in sequence
11. Always confirm what you found in your done response"""

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
    thread.join(timeout=45)  # Increased timeout for broader user directory search

    if thread.is_alive():
        return "Search timed out after 45 seconds. Try a more specific search pattern."
    elif exception[0]:
        return f"Search error: {str(exception[0])}"
    else:
        return result[0]

def _search_all_drives_impl(pattern):
    """Search across all available drives for files, focusing on user directories"""
    results = []
    drives = []

    pattern = pattern.strip()
    exact_wildcard = pattern
    if not any(ch in pattern for ch in ['*', '?', '[', ']']):
        exact_wildcard = f"*{pattern}*"

    # Detect all available drives and check accessibility
    import string
    for letter in string.ascii_uppercase:
        drive = f"{letter}:\\"
        if os.path.exists(drive):
            # Test if drive is actually accessible
            try:
                os.listdir(drive)  # Quick test for read access
                drives.append(drive)
            except (OSError, PermissionError):
                # Silently skip inaccessible drives
                continue

    if not drives:
        return "No accessible drives found for searching."

    print(f"Searching {len(drives)} accessible drives: {', '.join(drives)}", flush=True)

    total_found = 0

    # Define user and common directories to prioritize (not system directories)
    user_dirs = [
        "Users", "Documents and Settings", "home", "data",
        "Desktop", "Documents", "Downloads", "Pictures", "Videos", "Music",
        "AppData", "Local Settings", "Application Data", "My Documents"
    ]

    for drive in drives:
        found = []
        try:
            print(f"Scanning user areas on drive {drive}...", flush=True)

            def handle_access_error(error):
                # Silently skip directories we can't access
                pass

            # First, try to find and search user directories
            for root, dirs, files in os.walk(drive, topdown=True, onerror=handle_access_error):
                # Skip system directories entirely
                dirs[:] = [d for d in dirs if not any(skip.lower() in (os.path.join(root, d)).lower() for skip in [
                    'windows', 'program files', 'program files (x86)', 'programdata',
                    '$recycle.bin', 'system volume information', 'recovery', 'boot',
                    'msocache', 'inetpub', 'perflogs', 'temp', 'tmp'
                ])]

                # Check if this directory looks like a user area
                dir_name = os.path.basename(root)
                parent_name = os.path.basename(os.path.dirname(root)) if root != drive.rstrip('\\') else ""

                is_user_area = (
                    dir_name in user_dirs or
                    parent_name in user_dirs or
                    'user' in dir_name.lower() or
                    'home' in dir_name.lower() or
                    root.count(os.sep) >= 3  # Deeper directory structures more likely to be user data
                )

                if is_user_area or root == drive.rstrip('\\'):  # Always search drive root
                    for filename in files:
                        filepath = os.path.join(root, filename)
                        rel_root = os.path.relpath(root, drive)
                        rel_path = os.path.join(rel_root, filename) if rel_root != '.' else filename

                        if fnmatch.fnmatch(filename, exact_wildcard) or fnmatch.fnmatch(rel_path, pattern) or fnmatch.fnmatch(rel_path, exact_wildcard):
                            found.append(filepath)
                            total_found += 1
                            if total_found >= 100:  # Increased limit for broader search
                                break
                if total_found >= 100:
                    break

            if len(found) > 0:
                if len(found) >= 100:
                    results.append(f"Found 100+ files (showing first 100):")
                    found = found[:100]
                else:
                    results.append(f"Found {len(found)} file(s):")

                for file in sorted(found):
                    results.append(f"  {file}")
            else:
                results.append(f"No matching files found on {drive}")

        except Exception as e:
            results.append(f"Error searching {drive}: {str(e)}")

    if total_found == 0:
        return f"No files found matching '{pattern}' in user directories. Try a different search pattern or check file permissions."
    else:
        return "\n".join(results)

def open_file(filepath):
    """Open a file with the default application"""
    try:
        filepath = Path(filepath)
        if not filepath.exists():
            return f"File '{filepath}' does not exist"
        
        # Check if it's a safe file type to open
        safe_extensions = {'.txt', '.py', '.js', '.html', '.css', '.md', '.json', '.xml',
                          '.jpg', '.jpeg', '.png', '.gif', '.bmp', '.svg',
                          '.pdf', '.doc', '.docx', '.xls', '.xlsx', '.ppt', '.pptx',
                          '.log', '.ini', '.cfg', '.config', '.yaml', '.yml'}
        
        if filepath.suffix.lower() not in safe_extensions:
            return f"Cannot open file type '{filepath.suffix}'. Only safe file types are allowed."
        
        # Use os.startfile on Windows to open with default application
        os.startfile(str(filepath))
        return f"Opened '{filepath.name}' with default application"
    except Exception as e:
        return f"Error opening file: {str(e)}"

def read_file(filepath):
    """Read and display contents of a text file"""
    try:
        filepath = Path(filepath)
        if not filepath.exists():
            return f"File '{filepath}' does not exist"
        
        # Check if it's a text file
        text_extensions = {'.txt', '.py', '.js', '.html', '.css', '.md', '.json', '.xml', '.ini', '.cfg', '.config', '.yaml', '.yml', '.log'}
        
        if filepath.suffix.lower() not in text_extensions:
            return f"Cannot read file type '{filepath.suffix}'. Only text files are supported for reading."
        
        # Check file size (limit to 1MB)
        if filepath.stat().st_size > 1024 * 1024:
            return f"File '{filepath.name}' is too large to read ({filepath.stat().st_size} bytes). Maximum size is 1MB."
        
        # Read and return contents
        with open(filepath, 'r', encoding='utf-8', errors='replace') as f:
            content = f.read()
        
        return f"Contents of '{filepath.name}':\n\n{content}"
    except Exception as e:
        return f"Error reading file: {str(e)}"

def execute_file(filepath):
    """Execute a file with confirmation"""
    try:
        filepath = Path(filepath)
        if not filepath.exists():
            return f"File '{filepath}' does not exist"
        
        # Check if it's an executable file
        executable_extensions = {'.exe', '.msi', '.bat', '.cmd', '.ps1', '.vbs', '.jar'}
        
        if filepath.suffix.lower() not in executable_extensions:
            return f"Cannot execute file type '{filepath.suffix}'. Only executable files are allowed."
        
        # For executable files, request confirmation through the main system
        return f"CONFIRM_EXECUTION:{filepath}"
    except Exception as e:
        return f"Error preparing execution: {str(e)}"

def run_web_search(query):
    """Hand off web search to browser agent"""
    print(f"Handing off to browser agent for web search: {query}", flush=True)
    subprocess_kwargs = {
        "stdout": subprocess.PIPE,
        "stderr": subprocess.STDOUT,
        "text": True,
        "encoding": "utf-8",
        "bufsize": 1,
        "cwd": "C:\\container"
    }
    
    # Add creationflags only on Windows
    if platform.system() == "Windows":
        subprocess_kwargs["creationflags"] = 0x08000000
    
    process = subprocess.Popen(
        ["python", "-u", "ai_browser_native.py", query],
        **subprocess_kwargs
    )
    for line in process.stdout:
        line = line.strip()
        if line:
            print(line, flush=True)
    process.wait()

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

async def run_admin_task(task):
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

        if act == "search_system":
            pattern = action.get("pattern", "")
            path = action.get("path", "C:\\")
            
            # First search workspace recursively
            print("Searching workspace first...", flush=True)
            workspace_path = Path(WORKSPACE)
            if workspace_path.exists():
                workspace_pattern = str(workspace_path / "**" / pattern)
                workspace_files = glob.glob(workspace_pattern, recursive=True)
                
                if workspace_files:
                    print(f"Found {len(workspace_files)} file(s) in workspace:", flush=True)
                    for file in sorted(workspace_files):
                        print(f"  {file}", flush=True)
                    
                    # Check if this is a multi-step task
                    multi_step_indicators = [" then ", " and ", " after ", " next ", " followed by "]
                    is_multi_step = any(indicator in task.lower() for indicator in multi_step_indicators)
                    
                    if is_multi_step:
                        # Continue conversation for next step
                        messages.append({"role": "assistant", "content": raw})
                        messages.append({"role": "user", "content": f"Search completed:\nFound {len(workspace_files)} file(s) in workspace:\n" + "\n".join(f"- {file}" for file in sorted(workspace_files)) + f"\n\nThe user requested multiple steps. Choose the exact executable file path from the list above and perform the next action using execute_file. Do not search the web."})
                        continue
                    else:
                        # Single step task - end with done
                        messages.append({"role": "assistant", "content": raw})
                        messages.append({"role": "user", "content": f"Search completed:\nFound {len(workspace_files)} file(s) in workspace.\n\nNow respond to the user with done."})
                        continue
            
            print("No files found in workspace. Searching all drives...", flush=True)
            result = search_all_drives(pattern)
            print(result, flush=True)
            print("Drive search complete.", flush=True)
            
            # Check if this is a multi-step task (contains "then", "and", etc.)
            multi_step_indicators = [" then ", " and ", " after ", " next ", " followed by "]
            is_multi_step = any(indicator in task.lower() for indicator in multi_step_indicators)
            
            if is_multi_step:
                # Attempt to auto-select executable path for execute/run requests instead of relying on the model.
                if any(word in task.lower() for word in ["execute", "run", "launch", "start"]):
                    exe_candidates = [line.strip() for line in result.splitlines() if line.strip().lower().endswith('.exe')]
                    if exe_candidates:
                        target_name = os.path.basename(pattern).lower() if pattern else None
                        chosen = None
                        if target_name:
                            for exe in exe_candidates:
                                if target_name in os.path.basename(exe).lower():
                                    chosen = exe
                                    break
                        if not chosen:
                            chosen = exe_candidates[0]
                        print(f"Auto-selected executable for execution: {chosen}", flush=True)
                        print(execute_file(chosen), flush=True)
                        return
                
                # Continue conversation for next step
                messages.append({"role": "assistant", "content": raw})
                messages.append({"role": "user", "content": f"File search completed:\n{result}\n\nThe user requested multiple steps. Choose the exact executable file path from the results above and perform the next action using execute_file. Do not search the web."})
                continue
            else:
                # Single step task - end with done
                final_result = f"File search completed successfully. {result}"
                print(f"Result: {final_result}", flush=True)
                return

        elif act == "open_file":
            filepath = action.get("filepath", "")
            print(f"Opening file: {filepath}", flush=True)
            result = open_file(filepath)
            print(result, flush=True)
            messages.append({"role": "assistant", "content": raw})
            messages.append({"role": "user", "content": f"File operation completed: {result}\n\nNow respond to the user with done."})

        elif act == "read_file":
            filepath = action.get("filepath", "")
            print(f"Reading file: {filepath}", flush=True)
            result = read_file(filepath)
            print(result, flush=True)
            messages.append({"role": "assistant", "content": raw})
            messages.append({"role": "user", "content": f"File read completed: {result}\n\nNow respond to the user with done."})

        elif act == "execute_file":
            filepath = action.get("filepath", "")
            print(f"Preparing to execute: {filepath}", flush=True)
            print("WARNING: You are about to execute a file. This can be potentially dangerous.", flush=True)
            print(f"File: {filepath}", flush=True)
            
            # Emit a confirmation marker instead of trying to read stdin in the subprocess.
            print(f"CONFIRM_EXECUTION:{filepath}", flush=True)
            return

        elif act == "web_search":
            query = action.get("query", "")
            print(f"Performing web search for: {query}", flush=True)
            run_web_search(query)
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
    await run_admin_task(task)

def main():
    if len(sys.argv) > 1:
        task = sys.argv[1]
    else:
        print("No task provided.", flush=True)
        return

    asyncio.run(run(task))

if __name__ == "__main__":
    main()
