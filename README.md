# Jarvis Web Interface

A modern web-based AI assistant interface that replaces original Tkinter UI with a responsive, browser-based experience.

## Features

- **Web-based Interface**: Access from any device with a browser
- **Real-time Chat**: WebSocket-powered streaming responses
- **Modern UI**: Dark theme matching original design
- **Responsive Design**: Works on desktop, tablet, and mobile
- **Chat Persistence**: Saves conversations across sessions
- **Agent Integration**: Full compatibility with existing backend agents

## Quick Start

1. **Install Dependencies**
   ```bash
   pip install -r requirements.txt
   ```

2. **Run Locally**
   ```bash
   python app.py
   ```

3. **Access**
   Open http://localhost:5000 in your browser

## Deployment

### Railway (Recommended)
- Go to railway.app → Deploy from GitHub
- Select Jarvis repository

### Render
- Go to render.com → New Web Service
- Connect Jarvis repository
- Build: `pip install -r requirements.txt`
- Start: `gunicorn --worker-class eventlet -w 1 --bind 0.0.0.0:$PORT app:app`

### Heroku
- `heroku create app-name`
- `git push heroku main`

## File Structure

```
Jarvis/
├── app.py                 # Main Flask application
├── templates/
│   └── index.html         # Main HTML template
├── static/
│   ├── css/
│   │   └── style.css      # Stylesheets
│   └── js/
│       └── app.js         # Frontend JavaScript
├── brains.py              # AI routing logic
├── admin_agent.py         # System file operations
├── file_agent.py          # Workspace file operations  
├── ai_browser_native.py   # Web search functionality
├── chat_agent.py          # General conversation
├── requirements.txt       # Python dependencies
├── Dockerfile             # Docker configuration
├── docker-compose.yml     # Docker Compose setup
├── Procfile              # Heroku process definition
└── runtime.txt           # Python version for Heroku
```

## Configuration

The web interface integrates with the existing backend agents:

- **brains.py**: Intelligent request routing
- **admin_agent.py**: System-wide file searches
- **file_agent.py**: Workspace file operations  
- **ai_browser_native.py**: Web searches
- **chat_agent.py**: General conversation

## Contributing

1. Fork repository
2. Create a feature branch
3. Make your changes
4. Test thoroughly
5. Submit a pull request

## License

This project maintains the same license as the original Jarvis application.