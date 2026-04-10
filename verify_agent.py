import sys
import os
import json
from pathlib import Path

sys.stdout.reconfigure(encoding='utf-8')

# File to store confirmation context
CONTEXT_FILE = "C:\\container\\confirmation_context.json"

def save_confirmation_context(pattern, task):
    """Save the confirmation context for later retrieval"""
    context = {
        "pattern": pattern,
        "task": task,
        "timestamp": str(os.path.getmtime(__file__))
    }
    try:
        with open(CONTEXT_FILE, 'w') as f:
            json.dump(context, f)
    except Exception as e:
        print(f"Error saving context: {e}", flush=True)

def load_confirmation_context():
    """Load the confirmation context"""
    try:
        if os.path.exists(CONTEXT_FILE):
            with open(CONTEXT_FILE, 'r') as f:
                return json.load(f)
    except Exception as e:
        print(f"Error loading context: {e}", flush=True)
    return None

def clear_confirmation_context():
    """Clear the confirmation context"""
    try:
        if os.path.exists(CONTEXT_FILE):
            os.remove(CONTEXT_FILE)
    except Exception as e:
        print(f"Error clearing context: {e}", flush=True)

def get_confirmation(message, pattern, task):
    """Save confirmation context and prompt the user without requiring stdin"""
    print(message, flush=True)
    print(f"Would you like me to search your entire computer for '{pattern}'?", flush=True)
    print("This will search all drives and may take some time.", flush=True)
    print("Please reply with 'yes' to confirm or 'no' to cancel.", flush=True)
    
    # Save context for the confirmation and wait for the next chat response
    save_confirmation_context(pattern, task)
    return False

def handle_confirmation_response(response):
    """Handle the user's confirmation response with context"""
    context = load_confirmation_context()
    if not context:
        print("No pending confirmation found.", flush=True)
        return False
    
    response = response.strip().lower()
    if response in ['yes', 'y']:
        print("Confirmation received. Searching entire computer...", flush=True)
        # Clear the context since we're handling it
        clear_confirmation_context()
        # Return the pattern for searching
        return context['pattern']
    else:
        print("Search cancelled by user.", flush=True)
        clear_confirmation_context()
        return None

def get_execution_confirmation(filepath, task):
    """Save execution confirmation context and prompt the user"""
    print(f"⚠️  EXECUTION REQUEST ⚠️", flush=True)
    print(f"I found the executable: {filepath}", flush=True)
    print(f"WARNING: Executing files can be potentially dangerous and may harm your system.", flush=True)
    print(f"Are you sure you want to execute '{Path(filepath).name}'?", flush=True)
    print(f"Please reply with 'yes' to confirm execution or 'no' to cancel.", flush=True)
    
    # Save context for the confirmation
    context = {
        "filepath": filepath,
        "task": task,
        "type": "execution",
        "timestamp": str(os.path.getmtime(__file__))
    }
    try:
        with open(CONTEXT_FILE, 'w') as f:
            json.dump(context, f)
    except Exception as e:
        print(f"Error saving execution context: {e}", flush=True)

def handle_execution_confirmation(response):
    """Handle the user's execution confirmation response"""
    context = load_confirmation_context()
    if not context or context.get('type') != 'execution':
        print("No pending execution confirmation found.", flush=True)
        return False
    
    response = response.strip().lower()
    if response in ['yes', 'y']:
        print("Execution confirmation received.", flush=True)
        clear_confirmation_context()
        return context['filepath']
    else:
        print("Execution cancelled by user.", flush=True)
        clear_confirmation_context()
        return None
if len(sys.argv) > 1:
    command = sys.argv[1]
    
    if command == "confirm":
        # Request confirmation
        if len(sys.argv) > 2:
            pattern = sys.argv[2]
            task = " ".join(sys.argv[3:]) if len(sys.argv) > 3 else ""
            message = f"File '{pattern}' not found in workspace."
            result = get_confirmation(message, pattern, task)
            if result:
                sys.exit(0)
            # Pending confirmation: user must reply later through chat
            sys.exit(2)
        else:
            print("Missing pattern for confirmation.", flush=True)
            sys.exit(1)
    
    elif command == "confirm_execution":
        # Request execution confirmation
        if len(sys.argv) > 2:
            filepath = sys.argv[2]
            task = " ".join(sys.argv[3:]) if len(sys.argv) > 3 else ""
            get_execution_confirmation(filepath, task)
            # Pending confirmation: user must reply later through chat
            sys.exit(2)
        else:
            print("Missing filepath for execution confirmation.", flush=True)
            sys.exit(1)
    
    elif command == "execution_response":
        # Handle execution confirmation response
        if len(sys.argv) > 2:
            response = sys.argv[2]
            result = handle_execution_confirmation(response)
            if result:
                print(f"EXECUTION_FILE:{result}", flush=True)
                sys.exit(0)
            else:
                sys.exit(1)
        else:
            print("Missing response for execution confirmation.", flush=True)
            sys.exit(1)
    
    elif command == "response":
        # Handle user response
        if len(sys.argv) > 2:
            response = sys.argv[2]
            result = handle_confirmation_response(response)
            if result:
                print(f"SEARCH_PATTERN:{result}", flush=True)
                sys.exit(0)
            else:
                sys.exit(1)
        else:
            print("Missing response.", flush=True)
            sys.exit(1)
    
    # No else clause for unknown commands - let it fall through to usage

else:
    print("Usage: verify_agent.py <command> [args]", flush=True)
    print("Commands:", flush=True)
    print("  confirm <pattern> <task> - Request search confirmation", flush=True)
    print("  confirm_execution <filepath> <task> - Request execution confirmation", flush=True)
    print("  response <yes/no> - Handle search confirmation response", flush=True)
    print("  execution_response <yes/no> - Handle execution confirmation response", flush=True)
    sys.exit(1)
