#!/usr/bin/env python3
"""
Jarvis Web Deployment Script
Helps deploy the Jarvis web interface to various platforms
"""

import os
import sys
import subprocess
import json
from pathlib import Path

def run_command(command, check=True):
    """Run a command and return the result"""
    print(f"Running: {command}")
    result = subprocess.run(command, shell=True, capture_output=True, text=True)
    if check and result.returncode != 0:
        print(f"Error: {result.stderr}")
        sys.exit(1)
    return result

def check_prerequisites():
    """Check if all prerequisites are installed"""
    print("Checking prerequisites...")
    
    # Check if git is installed
    try:
        run_command("git --version")
    except:
        print("Error: Git is not installed. Please install Git first.")
        sys.exit(1)
    
    # Check if Docker is installed (optional)
    try:
        run_command("docker --version")
        print("[OK] Docker is installed")
    except:
        print("[!] Docker is not installed (optional for some deployment methods)")
    
    print("[OK] Prerequisites check complete")

def setup_git_repo():
    """Initialize Git repository if not already done"""
    if not Path(".git").exists():
        print("Initializing Git repository...")
        run_command("git init")
        run_command("git add .")
        run_command('git commit -m "Initial commit: Jarvis Web Interface"')
        print("[OK] Git repository initialized")
    else:
        print("[OK] Git repository already exists")

def deploy_heroku():
    """Deploy to Heroku"""
    print("\n=== Deploying to Heroku ===")
    
    # Check if Heroku CLI is installed
    try:
        run_command("heroku --version")
    except:
        print("Error: Heroku CLI is not installed.")
        print("Please install it from: https://devcenter.heroku.com/articles/heroku-cli")
        return False
    
    # Check if logged in to Heroku
    result = run_command("heroku auth:whoami", check=False)
    if result.returncode != 0:
        print("Please log in to Heroku first:")
        run_command("heroku login")
    
    # Create Heroku app
    app_name = input("Enter Heroku app name (leave blank for auto-generated): ").strip()
    if app_name:
        run_command(f"heroku create {app_name}")
    else:
        run_command("heroku create")
    
    # Deploy
    print("Deploying to Heroku...")
    run_command("git push heroku main")
    
    # Open the app
    run_command("heroku open")
    print("[OK] Deployed to Heroku successfully!")
    return True

def deploy_railway():
    """Deploy to Railway"""
    print("\n=== Deploying to Railway ===")
    print("To deploy to Railway:")
    print("1. Go to https://railway.app")
    print("2. Click 'New Project' → 'Deploy from GitHub repo'")
    print("3. Select this repository")
    print("4. Railway will automatically detect and deploy using the Dockerfile")
    print("5. Your app will be available at a random railway.app URL")
    return True

def deploy_render():
    """Deploy to Render"""
    print("\n=== Deploying to Render ===")
    print("To deploy to Render:")
    print("1. Go to https://render.com")
    print("2. Click 'New' → 'Web Service'")
    print("3. Connect your GitHub repository")
    print("4. Use these settings:")
    print("   - Build Command: pip install -r requirements.txt")
    print("   - Start Command: gunicorn --worker-class eventlet -w 1 --bind 0.0.0.0:$PORT app:app")
    print("   - Instance Type: Free")
    return True

def deploy_docker():
    """Deploy using Docker"""
    print("\n=== Deploying with Docker ===")
    
    # Build Docker image
    print("Building Docker image...")
    run_command("docker build -t jarvis-web .")
    
    # Run container
    print("Starting Docker container...")
    run_command("docker run -d -p 5000:5000 --name jarvis-web-container jarvis-web")
    
    print("[OK] Docker container is running!")
    print("Access your app at: http://localhost:5000")
    return True

def deploy_docker_compose():
    """Deploy using Docker Compose"""
    print("\n=== Deploying with Docker Compose ===")
    
    # Stop existing containers
    run_command("docker-compose down", check=False)
    
    # Start containers
    run_command("docker-compose up -d")
    
    print("[OK] Docker Compose services are running!")
    print("Access your app at: http://localhost:5000")
    return True

def create_github_repo():
    """Create and push to GitHub repository"""
    print("\n=== Setting up GitHub Repository ===")
    
    github_token = input("Enter your GitHub personal access token (or press Enter to skip): ").strip()
    repo_name = input("Enter repository name (e.g., username/jarvis-web): ").strip()
    
    if not github_token or not repo_name:
        print("Skipping GitHub setup")
        return False
    
    # Create repository using GitHub API
    import requests
    
    headers = {
        'Authorization': f'token {github_token}',
        'Accept': 'application/vnd.github.v3+json'
    }
    
    data = {
        'name': repo_name.split('/')[-1],
        'description': 'Jarvis Web Interface - Modern AI Assistant UI',
        'private': False
    }
    
    response = requests.post('https://api.github.com/user/repos', headers=headers, json=data)
    
    if response.status_code == 201:
        repo_url = f"https://github.com/{repo_name}.git"
        run_command(f"git remote add origin {repo_url}")
        run_command("git branch -M main")
        run_command(f"git push -u origin main")
        print(f"[OK] Repository created: {repo_url}")
        return True
    else:
        print(f"Error creating repository: {response.text}")
        return False

def main():
    """Main deployment menu"""
    print("Jarvis Web Interface Deployment Tool")
    print("=" * 50)
    
    check_prerequisites()
    setup_git_repo()
    
    while True:
        print("\nChoose deployment option:")
        print("1. Heroku (Free tier available)")
        print("2. Railway (Free tier available)")
        print("3. Render (Free tier available)")
        print("4. Docker (Local deployment)")
        print("5. Docker Compose (Local deployment)")
        print("6. Setup GitHub Repository")
        print("7. Exit")
        
        choice = input("\nEnter your choice (1-7): ").strip()
        
        if choice == "1":
            deploy_heroku()
        elif choice == "2":
            deploy_railway()
        elif choice == "3":
            deploy_render()
        elif choice == "4":
            deploy_docker()
        elif choice == "5":
            deploy_docker_compose()
        elif choice == "6":
            create_github_repo()
        elif choice == "7":
            print("Goodbye!")
            break
        else:
            print("Invalid choice. Please try again.")

if __name__ == "__main__":
    main()
