from flask import Flask, render_template, request, jsonify, session
from flask_socketio import SocketIO, emit
import json
import os
import subprocess
import threading
import asyncio
from datetime import datetime
import uuid
import sys

app = Flask(__name__)
app.config['SECRET_KEY'] = 'jarvis-web-interface-secret-key'
socketio = SocketIO(app, cors_allowed_origins="*")

# Chat storage
CHATS_FILE = "C:\\container\\chats.json"
ACTIVE_SESSIONS = {}

def load_chats():
    if os.path.exists(CHATS_FILE):
        with open(CHATS_FILE, "r") as f:
            return json.load(f)
    return {}

def save_chats(chats):
    with open(CHATS_FILE, "w") as f:
        json.dump(chats, f, indent=2)

def run_agent_task(task, session_id):
    """Run agent task in background thread and emit results via WebSocket"""
    try:
        # Use brains.py for intelligent routing
        script = "brains.py"
        
        process = subprocess.Popen(
            ["python", "-u", script, task],
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,
            text=True,
            bufsize=0,
            cwd="C:\\container",
            creationflags=0x08000000
        )
        
        # Read output line by line and emit to client
        for line in process.stdout:
            line_content = line.rstrip('\n\r')
            if line_content.strip():
                socketio.emit('agent_response', {
                    'session_id': session_id,
                    'message': line_content,
                    'type': 'stream'
                })
        
        process.wait()
        
        # Signal completion
        socketio.emit('agent_response', {
            'session_id': session_id,
            'message': '',
            'type': 'complete'
        })
        
    except Exception as e:
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
    return jsonify({'error': 'Chat not found'}), 404

@app.route('/api/chats', methods=['POST'])
def create_chat():
    chats = load_chats()
    chat_id = datetime.now().strftime("%Y%m%d_%H%M%S")
    opener = "Hello! I'm Jarvis, your AI assistant. How can I help you today?"
    
    chats[chat_id] = {
        "title": "New chat",
        "messages": [{"sender": "Agent", "text": opener, "timestamp": datetime.now().isoformat()}],
        "created": datetime.now().strftime("%b %d, %H:%M")
    }
    
    save_chats(chats)
    return jsonify({'chat_id': chat_id, 'chat': chats[chat_id]})

@app.route('/api/chats/<chat_id>', methods=['DELETE'])
def delete_chat(chat_id):
    chats = load_chats()
    if chat_id in chats:
        del chats[chat_id]
        save_chats(chats)
        return jsonify({'success': True})
    return jsonify({'error': 'Chat not found'}), 404

@app.route('/api/chats/<chat_id>/messages', methods=['POST'])
def add_message(chat_id):
    chats = load_chats()
    if chat_id not in chats:
        return jsonify({'error': 'Chat not found'}), 404
    
    data = request.get_json()
    message = data.get('message', '')
    sender = data.get('sender', 'You')
    
    # Add user message
    chats[chat_id]["messages"].append({
        "sender": sender,
        "text": message,
        "timestamp": datetime.now().isoformat()
    })
    
    # Update title if this is the first user message
    if len(chats[chat_id]["messages"]) == 2:  # Agent opener + this message
        title = message[:24] + ("..." if len(message) > 24 else "")
        chats[chat_id]["title"] = title
    
    save_chats(chats)
    
    # Start agent task in background
    session_id = str(uuid.uuid4())
    ACTIVE_SESSIONS[session_id] = chat_id
    
    thread = threading.Thread(target=run_agent_task, args=(message, session_id))
    thread.daemon = True
    thread.start()
    
    return jsonify({'success': True, 'session_id': session_id})

@socketio.on('connect')
def handle_connect():
    print('Client connected')

@socketio.on('disconnect')
def handle_disconnect():
    print('Client disconnected')

if __name__ == '__main__':
    if not os.path.exists('templates'):
        os.makedirs('templates')
    if not os.path.exists('static'):
        os.makedirs('static')
        os.makedirs('static\\css')
        os.makedirs('static\\js')
    
    socketio.run(app, host='0.0.0.0', port=5000, debug=True)
