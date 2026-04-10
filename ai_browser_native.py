import asyncio
import sys
import os
import json
import httpx
import re
sys.stdout.reconfigure(encoding='utf-8')
from camoufox.async_api import AsyncCamoufox

WORKSPACE = "C:\\container\\workspace"
OLLAMA_URL = "http://localhost:11434/api/chat"
MODEL = "nous-hermes2:10.7b"

SYSTEM_PROMPT = """You are Jarvis, a web research agent. You MUST respond with ONLY a single JSON object, nothing else.

Available actions:
{ "action": "goto", "url": "https://..." }
{ "action": "done", "result": "your full answer here" }

RULES:
1. ALWAYS start by doing: goto https://duckduckgo.com/?q=search+terms+here
2. After seeing search results, pick ONE good link and goto it directly using the full URL from the links list
3. After reading a page, if you have enough info use done with a complete answer
4. If you need more info, goto another URL
5. NEVER use click or type - only use goto and done
6. NEVER go to YouTube, Steam, Reddit or social media
7. When you use done, write a full detailed answer in plain English"""

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

async def ask_ollama(messages):
    print("Thinking...")
    async with httpx.AsyncClient(timeout=90) as client:
        response = await client.post(OLLAMA_URL, json={
            "model": MODEL,
            "messages": messages,
            "stream": False,
            "format": "json"
        })
        data = response.json()
        return data["message"]["content"]

async def extract_page_content(page):
    try:
        title = await page.title()
        result = await page.evaluate("""() => {
            const main = document.querySelector('main, article, #content, .content, body');
            const text = main ? main.innerText.slice(0, 2000) : document.body.innerText.slice(0, 2000);
            const links = [];
            document.querySelectorAll('a[href]').forEach(a => {
                const href = a.href;
                const label = a.innerText.trim().slice(0, 60);
                if (href.startsWith('http') && label &&
                    !href.includes('youtube') && !href.includes('facebook') &&
                    !href.includes('twitter') && !href.includes('steam') &&
                    !href.includes('reddit')) {
                    links.push(label + ' -> ' + href);
                }
            });
            return { text: text, links: links.slice(0, 10).join('\\n') };
        }""")
        return f"Page title: {title}\n\nContent:\n{result['text']}\n\nLinks:\n{result['links']}"
    except:
        return "Could not extract page content"

async def force_summary(messages, task):
    print("\nSummarizing findings...")
    summary_messages = [messages[0]] + messages[1:] + [{
        "role": "user",
        "content": f"You have finished researching. Now write a complete answer to: {task}\nRespond with only this JSON: {{\"action\": \"done\", \"result\": \"write your full answer here\"}}"
    }]
    raw = await ask_ollama(summary_messages)
    try:
        parsed = json.loads(raw)
        result = parsed.get("result", "")
        if result and len(result) > 20:
            return result
        for val in parsed.values():
            if isinstance(val, str) and len(val) > 20:
                return val
    except:
        pass
    return "Research complete but could not generate summary. Check the steps above for information found."

async def run_browser_task(task):
    messages = [
        {"role": "system", "content": SYSTEM_PROMPT},
        {"role": "user", "content": f"Research this and give me a full answer: {task}"}
    ]

    print(f"Starting task: {task}")
    print("Launching browser...")

    async with AsyncCamoufox(headless=True, humanize=True) as browser:
        page = await browser.new_page()
        print("Browser ready\n")

        for step in range(20):
            print(f"Step {step + 1} of 20")
            raw = await ask_ollama(messages)

            # Parse JSON
            action = None
            try:
                action = json.loads(raw)
            except json.JSONDecodeError:
                match = re.search(r'\{[^{}]*\}', raw, re.DOTALL)
                if match:
                    try:
                        action = json.loads(match.group(0))
                    except:
                        pass

            if not action:
                print("Could not parse response, summarizing...")
                result = await force_summary(messages, task)
                print(f"\nResult: {result}")
                return

            act = action.get("action", "")

            if act == "goto":
                url = action.get("url", "")
                if "duckduckgo.com/?q=" in url:
                    query = url.split("?q=")[1].split("&")[0].replace("+", " ")
                    print(f"Searching the web for: {query}")
                else:
                    print(f"Visiting {url}")
                try:
                    await page.goto(url, wait_until="domcontentloaded", timeout=20000)
                    await asyncio.sleep(1)
                    content = await extract_page_content(page)
                    print("Page loaded successfully")
                    messages.append({"role": "assistant", "content": raw})
                    messages.append({"role": "user", "content": f"Page loaded. Here is what I found:\n{content}\n\nIf you have enough info to answer the task, use done. Otherwise goto another URL from the links list."})
                except Exception as e:
                    print("Could not load that page, will try another")
                    messages.append({"role": "assistant", "content": raw})
                    messages.append({"role": "user", "content": f"Failed to load {url}. Please try a different URL."})

            elif act == "done":
                result = action.get("result", "")
                if result and len(result) > 20:
                    print(f"\nResult: {result}")
                else:
                    print("Answer too short, asking for more detail...")
                    messages.append({"role": "assistant", "content": raw})
                    messages.append({"role": "user", "content": "Your answer was too short. Please provide a complete detailed answer using done."})
                    continue
                return

            else:
                print(f"Unexpected action, reminding AI of rules...")
                messages.append({"role": "assistant", "content": raw})
                messages.append({"role": "user", "content": "Remember: only use goto or done actions. Use goto with a URL to visit pages, or done with your complete answer."})

        print("Reached step limit, summarizing...")
        result = await force_summary(messages, task)
        print(f"\nResult: {result}")

async def run(task: str):
    task_lower = task.lower()

    if "list files" in task_lower or "what's in the workspace" in task_lower:
        print(list_files())
        return
    if task_lower.startswith("read "):
        print(read_file(task.split(" ", 1)[1].strip()))
        return
    if task_lower.startswith("write "):
        parts = task.split(" ", 2)
        if len(parts) >= 3:
            print(write_file(parts[1].strip(), parts[2].strip()))
        return
    if task_lower.startswith("save "):
        parts = task.split(" to ", 1)
        if len(parts) == 2:
            print(write_file(parts[1].strip(), parts[0].replace("save ", "", 1).strip()))
        return

    await run_browser_task(task)

if len(sys.argv) > 1:
    task = sys.argv[1]
else:
    print("No task provided. Please use the UI.")
    exit()

asyncio.run(run(task))