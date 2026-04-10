# Jarvis Web Interface - Deployment

Repository: https://github.com/e91707-spec/Jarvis

## Quick Deploy

### Railway (Recommended)
- Go to railway.app → New Project → Deploy from GitHub
- Select Jarvis repository
- Auto-deploys with Dockerfile

### Render
- Go to render.com → New Web Service
- Connect Jarvis repository
- Build: `pip install -r requirements.txt`
- Start: `gunicorn --worker-class eventlet -w 1 --bind 0.0.0.0:$PORT app:app`

### Heroku
- `heroku create app-name`
- `git push heroku main`
