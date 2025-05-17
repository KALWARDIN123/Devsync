<<<<<<< HEAD
# DevSync - Developer Collaboration Platform

DevSync is a modern platform designed to enhance developer collaboration through features like code review, standups, and team management.

## 🚀 Features

- Team Management & Collaboration
- Real-time Chat & Notifications
- AI-Powered Code Reviews
- Daily Standups
- Project Analytics
- Task Management

## 🛠️ Tech Stack

- **Backend**: Django 4.2+
- **Database**: PostgreSQL
- **Cache & Message Broker**: Redis
- **Real-time**: Django Channels
- **AI Integration**: OpenAI
- **Frontend Enhancement**: HTMX, TailwindCSS
- **Task Queue**: Celery

## 📁 Project Structure

```
devsync/
├── requirements/               # Split requirements files
│   ├── base.txt              # Base dependencies
│   ├── local.txt             # Development dependencies
│   └── production.txt        # Production dependencies
├── config/                    # Project configuration
│   ├── settings/             # Split settings files
│   ├── urls.py              
│   └── asgi.py              # ASGI config for Channels
├── core/                     # Core functionality
│   ├── models.py            # Base models
│   └── views.py             # Core views
├── ai/                      # AI integration
│   └── services/           # AI services
├── chat/                    # Real-time chat
│   └── consumers.py        # WebSocket consumers
├── analytics/              # Analytics features
├── tasks/                  # Task management
├── templates/              # HTML templates
├── static/                 # Static files
│   ├── css/               # Styled components
│   └── js/                # JavaScript modules
└── manage.py
```

## 🚀 Setup & Installation

1. Clone the repository:
```bash
git clone https://github.com/yourusername/devsync.git
cd devsync
```

2. Create and activate virtual environment:
```bash
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
```

3. Install dependencies:
```bash
pip install -r requirements/local.txt
```

4. Set up environment variables:
```bash
cp .env.example .env
# Edit .env with your configuration
```

5. Run migrations:
```bash
python manage.py migrate
```

6. Start Redis server:
```bash
redis-server
```

7. Run Celery worker:
```bash
celery -A devsync worker -l info
```

8. Start development server:
```bash
python manage.py runserver
```

## 🔧 Configuration

### Environment Variables

Create a `.env` file in the root directory with:

```
DEBUG=True
SECRET_KEY=your-secret-key
DATABASE_URL=postgres://user:password@localhost:5432/devsync
REDIS_URL=redis://localhost:6379/0
OPENAI_API_KEY=your-openai-key
```

### Database Setup

1. Install PostgreSQL
2. Create database:
```sql
CREATE DATABASE devsync;
```

## 📦 Deployment

The application is configured for deployment on cloud platforms with:

- Gunicorn as WSGI server
- Daphne as ASGI server
- WhiteNoise for static files
- Redis for caching and Channels

## 🔄 CI/CD Pipeline

- GitHub Actions for automated testing
- Docker containers for consistent environments
- Automated deployments to staging/production

## 📝 Contributing

1. Fork the repository
2. Create your feature branch
3. Commit your changes
4. Push to the branch
5. Create a Pull Request

## 📄 License

This project is licensed under the MIT License. 
=======
# Devsync-Test-
Discord For Devs
>>>>>>> 4c82054d3ac78179bd84befb51edb4d8a18c5a95
