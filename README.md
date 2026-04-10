# Jarvis Web Interface

A modern web-based AI assistant interface that replaces the original Tkinter UI with a responsive, browser-based experience.

## Features

- **Web-based Interface**: Access from any device with a browser
- **Real-time Chat**: WebSocket-powered streaming responses
- **Modern UI**: Dark theme matching the original design
- **Responsive Design**: Works on desktop, tablet, and mobile
- **Chat Persistence**: Saves conversations across sessions
- **Agent Integration**: Full compatibility with existing backend agents

## Quick Start

### Local Development

1. **Clone and Setup**
   ```bash
   git clone https://github.com/e91707-spec/Jarvis.git
   cd Jarvis
   ```

2. **Install Dependencies**
   ```bash
   pip install -r requirements.txt
   ```

3. **Run Locally**
   ```bash
   python launch_web.py
   ```
   Or directly:
   ```bash
   python app.py
   ```

4. **Access**
   Open http://localhost:5000 in your browser

### Docker Deployment

1. **Build and Run**
   ```bash
   docker-compose up -d
   ```

2. **Access**
   Open http://localhost:5000 in your browser

## Deployment Options

### 1. Railway (Easiest - Free)

1. **Connect GitHub Repo**
   - Go to [railway.app](https://railway.app)
   - Click "New Project" → "Deploy from GitHub repo"
   - Select your "Jarvis" repository

2. **Configure**
   - Railway will automatically detect Dockerfile
   - Set environment variables if needed

### 2. Render (Free)

1. **Create Web Service**
   - Go to [render.com](https://render.com)
   - Click "New" → "Web Service"
   - Connect your GitHub repository

2. **Configure**
   - Build Command: `pip install -r requirements.txt`
   - Start Command: `gunicorn --worker-class eventlet -w 1 --bind 0.0.0.0:$PORT app:app`
   - Instance Type: Free

### 3. Heroku (Free)

1. **Create Heroku App**
   ```bash
   heroku create your-app-name
   ```

2. **Deploy**
   ```bash
   git push heroku main
   ```

3. **Access**
   Your app will be available at `https://your-app-name.herokuapp.com`

### 4. VPS/Dedicated Server

1. **Install Docker**
   ```bash
   curl -fsSL https://get.docker.com -o get-docker.sh
   sh get-docker.sh
   ```

2. **Deploy**
   ```bash
   git clone https://github.com/e91707-spec/Jarvis.git
   cd Jarvis
   docker-compose up -d
   ```

3. **Setup Reverse Proxy (Optional)**
   Use Nginx or Apache to proxy to port 5000

## Environment Variables

Create a `.env` file for local development:

```env
FLASK_ENV=development
SECRET_KEY=your-secret-key-here
OLLAMA_URL=http://localhost:11434/api/chat
MODEL=nous-hermes2:10.7b
```

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

### Backend Agents

The web interface integrates with the existing backend agents:

- **brains.py**: Intelligent request routing
- **admin_agent.py**: System-wide file searches
- **file_agent.py**: Workspace file operations  
- **ai_browser_native.py**: Web searches
- **chat_agent.py**: General conversation

### Chat Storage

Chats are stored in `chats.json` in the project root. For production, consider:

- Database storage (PostgreSQL, MongoDB)
- Cloud storage (AWS S3, Google Cloud Storage)
- Redis for session management

## Security Considerations

1. **Environment Variables**: Never commit secrets to Git
2. **Input Validation**: Sanitize all user inputs
3. **Rate Limiting**: Implement rate limiting for API endpoints
4. **HTTPS**: Always use HTTPS in production
5. **Authentication**: Add user authentication if needed

## Troubleshooting

### Common Issues

1. **WebSocket Connection Failed**
   - Check if port 5000 is open
   - Verify firewall settings
   - Ensure WebSocket support in hosting environment

2. **Agent Responses Not Working**
   - Verify Ollama is running and accessible
   - Check `OLLAMA_URL` environment variable
   - Ensure all agent files are present and executable

3. **Deployment Issues**
   - Check build logs for dependency errors
   - Verify Python version compatibility
   - Ensure all required files are included

### Logs

- **Local Development**: Check terminal output
- **Docker**: `docker-compose logs -f`
- **Heroku**: `heroku logs --tail`
- **Railway**: Check deployment logs in dashboard

## Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Test thoroughly
5. Submit a pull request

## License

This project maintains the same license as the original Jarvis application.

## Support

For issues and questions:
1. Check this README
2. Review the troubleshooting section
3. Open an issue on GitHub
