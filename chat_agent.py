import asyncio
import sys
import os
import json
import httpx
import re
sys.stdout.reconfigure(encoding='utf-8')

OLLAMA_URL = "http://localhost:11434/api/chat"
MODEL = "nous-hermes2:10.7b"

SYSTEM_PROMPT = """You are Jarvis, a helpful AI assistant. You respond naturally and conversationally to user questions and requests.

You can help with:
- Answering questions and providing information
- Helping with programming and technical problems
- Writing code and explaining concepts
- General conversation and assistance

Be friendly, helpful, and provide detailed, accurate responses. If you don't know something, say so honestly.
Always respond in a natural, conversational way - not in JSON format.
Introduce yourself as Jarvis when appropriate, but don't overdo it."""

async def ask_ollama(messages):
    print("Thinking...", flush=True)
    try:
        async with httpx.AsyncClient(timeout=120) as client:  # Increased timeout
            response = await client.post(OLLAMA_URL, json={
                "model": MODEL,
                "messages": messages,
                "stream": False,
                "options": {
                    "temperature": 0.7,
                    "top_p": 0.9,
                    "max_tokens": 2048  # Ensure sufficient tokens for long responses
                }
            })
            response.raise_for_status()
            data = response.json()
            return data["message"]["content"]
    except httpx.HTTPStatusError as e:
        print(f"HTTP error: {e}", flush=True)
        return "Sorry, I'm having trouble connecting to my brain. Please try again."
    except Exception as e:
        print(f"Error: {e}", flush=True)
        return "Sorry, something went wrong. Please try again."

async def run_chat_task(task):
    messages = [
        {"role": "system", "content": SYSTEM_PROMPT},
        {"role": "user", "content": task}
    ]
    
    try:
        response = await ask_ollama(messages)
        # Ensure response is fully printed
        if response:
            print(response, flush=True)
            sys.stdout.flush()  # Force output to be written immediately
        else:
            print("I received an empty response. Please try again.", flush=True)
    except Exception as e:
        error_msg = f"Error getting AI response: {str(e)}"
        print(error_msg, flush=True)
        sys.stdout.flush()

async def run(task: str):
    await run_chat_task(task)

def main():
    if len(sys.argv) > 1:
        task = sys.argv[1]
    else:
        print("No task provided.", flush=True)
        return

    asyncio.run(run(task))

if __name__ == "__main__":
    main()
