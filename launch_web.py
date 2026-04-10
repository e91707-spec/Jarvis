import subprocess
import sys
import os
import webbrowser
import time
from threading import Timer

def open_browser():
    """Open browser after a short delay to ensure server is running"""
    time.sleep(2)
    webbrowser.open('http://localhost:5000')

def main():
    os.chdir("C:\\container")
    
    print("Starting Jarvis Web Interface...")
    print("Installing dependencies...")
    
    # Install requirements
    try:
        subprocess.check_call([sys.executable, "-m", "pip", "install", "-r", "requirements.txt"])
        print("Dependencies installed successfully!")
    except subprocess.CalledProcessError as e:
        print(f"Error installing dependencies: {e}")
        return
    
    print("Starting web server...")
    print("The web interface will open in your browser automatically.")
    print("If it doesn't open, navigate to: http://localhost:5000")
    
    # Open browser in a separate thread
    Timer(2, open_browser).start()
    
    # Start the Flask app
    try:
        subprocess.call([sys.executable, "app.py"])
    except KeyboardInterrupt:
        print("\nShutting down web server...")
    except Exception as e:
        print(f"Error starting web server: {e}")

if __name__ == "__main__":
    main()
