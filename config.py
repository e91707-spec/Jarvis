import os
import platform
from pathlib import Path

def get_base_directory():
    """Get the base directory for the application"""
    if platform.system() == "Windows":
        return "C:\\container"
    else:
        # For Render and other cloud platforms
        return "/opt/render/project/src"

def get_workspace_directory():
    """Get the workspace directory"""
    base_dir = get_base_directory()
    workspace_dir = os.path.join(base_dir, "workspace")
    
    # Create workspace if it doesn't exist
    Path(workspace_dir).mkdir(parents=True, exist_ok=True)
    return workspace_dir

def get_chats_file():
    """Get the chats file path"""
    base_dir = get_base_directory()
    chats_file = os.path.join(base_dir, "chats.json")
    
    # Create base directory if it doesn't exist
    Path(base_dir).mkdir(parents=True, exist_ok=True)
    return chats_file

# Export paths
BASE_DIR = get_base_directory()
WORKSPACE = get_workspace_directory()
CHATS_FILE = get_chats_file()

# For backward compatibility
if platform.system() == "Windows":
    WORKSPACE = "C:\\container\\workspace"
    CHATS_FILE = "C:\\container\\chats.json"
