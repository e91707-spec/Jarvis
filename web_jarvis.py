from flask import Flask, render_template, request, jsonify, session
from flask_socketio import SocketIO, emit
import json
import os
import threading
import asyncio
import httpx
from datetime import datetime
import uuid
import sys

# Standalone Groq Client (no external imports)
class GroqClient:
    def __init__(self):
        self.api_key = os.getenv("GROQ_API_KEY")
        self.base_url = os.getenv("GROQ_BASE_URL", "https://api.groq.com/openai/v1")
        self.model = os.getenv("GROQ_MODEL", "llama-3.1-8b-instant")
        
        if not self.api_key:
            raise ValueError("GROQ_API_KEY environment variable is required")
    
    async def chat_completion(self, messages, stream=False, json_mode=False):
        """Send chat completion request to Groq API"""
        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json"
        }
        
        payload = {
            "model": self.model,
            "messages": messages,
            "stream": stream
        }
        
        if json_mode:
            payload["response_format"] = {"type": "json_object"}
        
        async with httpx.AsyncClient(timeout=90) as client:
            response = await client.post(
                f"{self.base_url}/chat/completions",
                headers=headers,
                json=payload
            )
            
            if response.status_code != 200:
                error_msg = f"Groq API error: {response.status_code} - {response.text}"
                print(error_msg, flush=True)
                raise Exception(error_msg)
            
            data = response.json()
            return data["choices"][0]["message"]["content"]

# Global Groq client instance
groq_client = GroqClient()

app = Flask(__name__)
app.config['SECRET_KEY'] = 'jarvis-web-interface-secret-key'
socketio = SocketIO(app, cors_allowed_origins="*")

# In-memory chat storage (no files!)
ACTIVE_SESSIONS = {}
CHAT_MEMORY = {}  # In-memory storage for all chats

def load_chats():
    """Load chats from memory (file-free)"""
    return CHAT_MEMORY

def save_chats(chats):
    """Save chats to memory (file-free)"""
    global CHAT_MEMORY
    CHAT_MEMORY = chats.copy()

async def run_agent_task(task, session_id):
    """Run agent task directly using Groq API (no subprocess)"""
    try:
        print(f"Processing task: {task}", flush=True)
        
        # Use Groq API directly for chat
        messages = [
            {"role": "system", "content": """You are Jarvis, a helpful AI assistant. You respond naturally and conversationally to user questions and requests.

You can help with:
- Answering questions and providing information
- Helping with programming and technical problems
- Writing code and explaining concepts
- General conversation and assistance

Be friendly, helpful, and provide detailed, accurate responses. If you don't know something, say so honestly.
Always respond in a natural, conversational way - not in JSON format.
Introduce yourself as Jarvis when appropriate, but don't overdo it."""},
            {"role": "user", "content": task}
        ]
        
        # Get response from Groq API
        response = await groq_client.chat_completion(messages)
        
        # Collect all output for saving
        all_output = [response]
        
        # Stream the response to client
        for line in response.split('\n'):
            if line.strip():
                socketio.emit('agent_response', {
                    'session_id': session_id,
                    'message': line,
                    'type': 'stream'
                })
        
        # Save the chat
        if session_id in ACTIVE_SESSIONS:
            chat_id = ACTIVE_SESSIONS[session_id]
            chats = load_chats()
            if chat_id not in chats:
                chats[chat_id] = {
                    "title": task[:24] + ("..." if len(task) > 24 else ""),
                    "messages": [],
                    "created": datetime.now().strftime("%b %d, %H:%M")
                }
            
            chats[chat_id]["messages"].append({
                "sender": "Agent",
                "text": response,
                "timestamp": datetime.now().isoformat()
            })
            save_chats(chats)
        
        # Signal completion with the final text
        socketio.emit('agent_response', {
            'session_id': session_id,
            'message': response,
            'type': 'complete'
        })
        
    except Exception as e:
        print(f"Error in agent task: {str(e)}", flush=True)
        socketio.emit('agent_response', {
            'session_id': session_id,
            'message': f"Error: {str(e)}",
            'type': 'error'
        })

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/api/chats', methods=['GET'])
def get_chats():
    chats = load_chats()
    return jsonify(chats)

@app.route('/api/chats/<chat_id>', methods=['GET'])
def get_chat(chat_id):
    chats = load_chats()
    if chat_id in chats:
        return jsonify(chats[chat_id])
    return jsonify({"error": "Chat not found"}), 404

@app.route('/api/chats', methods=['POST'])
def create_chat():
    chats = load_chats()
    chat_id = str(uuid.uuid4())
    opener = "Hello! I'm Jarvis, your AI assistant. How can I help you today?"
    
    chats[chat_id] = {
        "title": "New chat",
        "messages": [{"sender": "Agent", "text": opener, "timestamp": datetime.now().isoformat()}],
        "created": datetime.now().strftime("%b %d, %H:%M")
    }
    save_chats(chats)
    return jsonify({"chat_id": chat_id, "chat": chats[chat_id]})

@app.route('/api/chats/<chat_id>', methods=['DELETE'])
def delete_chat(chat_id):
    chats = load_chats()
    if chat_id in chats:
        del chats[chat_id]
        save_chats(chats)
        return jsonify({"success": True})
    return jsonify({"error": "Chat not found"}), 404

@socketio.on('send_message')
def handle_message(data):
    task = data.get('message', '')
    session_id = data.get('session_id')
    chat_id = data.get('chat_id')
    
    if not task or not session_id:
        return
    
    # Store session mapping
    ACTIVE_SESSIONS[session_id] = chat_id
    
    # Save user message
    chats = load_chats()
    if chat_id not in chats:
        chats[chat_id] = {
            "title": task[:24] + ("..." if len(task) > 24 else ""),
            "messages": [],
            "created": datetime.now().strftime("%b %d, %H:%M")
        }
    
    chats[chat_id]["messages"].append({
        "sender": "You",
        "text": task,
        "timestamp": datetime.now().isoformat()
    })
    save_chats(chats)
    
    # Start processing in background
    def run_async_task():
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        try:
            loop.run_until_complete(run_agent_task(task, session_id))
        finally:
            loop.close()
    
    threading.Thread(target=run_async_task, daemon=True).start()

@socketio.on('connect')
def handle_connect():
    print('Client connected', flush=True)

@socketio.on('disconnect')
def handle_disconnect():
    print('Client disconnected', flush=True)

if __name__ == '__main__':
    print("Starting Jarvis Web Interface (File-Free Version)", flush=True)
    socketio.run(app, host='0.0.0.0', port=5000, debug=False)
