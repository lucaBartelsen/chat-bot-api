# File: README.md
# Path: fanfix-api/README.md

# FanFix ChatAssist API

A FastAPI-based backend for generating AI-powered chat suggestions for creators on the FanFix platform.

## Tech Stack

- **FastAPI**: Modern, high-performance web framework for building APIs with Python
- **Prisma**: Next-generation ORM for Python and Node.js
- **PostgreSQL with pgvector**: Database with vector search capabilities
- **OpenAI API**: For generating conversation suggestions and embeddings
- **LangChain**: Framework for building LLM-powered applications
- **FastAPI Users**: Authentication and user management

## Features

- JWT Authentication
- User preferences management
- Creator profile management
- Creator writing style customization
- AI-powered conversation suggestions
- Vector-based similar conversation search
- Multi-message suggestion format

## Prerequisites

- Python 3.9+
- PostgreSQL 14+ with pgvector extension
- OpenAI API key

## Installation

1. Clone the repository:
   ```bash
   git clone https://github.com/your-username/fanfix-api.git
   cd fanfix-api
   ```

2. Create and activate a virtual environment:
   ```bash
   python -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   ```

3. Install dependencies:
   ```bash
   pip install -r requirements.txt
   ```

4. Setup environment variables:
   ```bash
   cp .env.example .env
   # Edit .env file with your configuration
   ```

5. Initialize and migrate the database:
   ```bash
   # Install pgvector extension in your PostgreSQL database
   psql -U postgres -d chat_assistant_db -c "CREATE EXTENSION IF NOT EXISTS vector;"
   
   # Generate Prisma client
   prisma db push
   prisma generate
   ```

## Running the Application

For development:
```bash
uvicorn main:app --reload
```

For production:
```bash
uvicorn main:app --host 0.0.0.0 --port 8000
```

The API will be available at http://localhost:8000, and the interactive documentation at http://localhost:8000/docs.

## API Endpoints

### Authentication

- `POST /api/auth/register`: Register a new user
- `POST /api/auth/login`: Login to get an access token
- `GET /api/auth/me`: Get current user info
- `GET /api/auth/preferences`: Get user preferences
- `PATCH /api/auth/preferences`: Update user preferences

### Creators

- `GET /api/creators`: Get all creators
- `GET /api/creators/{creator_id}`: Get a specific creator
- `POST /api/creators`: Create a new creator
- `PATCH /api/creators/{creator_id}`: Update a creator
- `POST /api/creators/{creator_id}/style`: Create or update a creator's style
- `POST /api/creators/{creator_id}/examples`: Add a style example for a creator
- `GET /api/creators/{creator_id}/examples`: Get style examples for a creator

### Suggestions

- `POST /api/suggestions`: Get suggestions for a fan message
- `GET /api/suggestions/stats`: Get statistics about stored conversations
- `POST /api/suggestions/clear`: Clear stored conversations

## Development

### Project Structure

```
fanfix-api/
├── .env                  # Environment variables
├── main.py               # FastAPI entrypoint
├── prisma/
│   └── schema.prisma     # Prisma schema
├── app/
│   ├── api/              # API routes
│   │   ├── auth.py       # Auth endpoints
│   │   ├── creators.py   # Creator management
│   │   └── suggestions.py # Suggestion endpoints
│   ├── core/             # Core config
│   │   ├── config.py     # Settings
│   │   └── security.py   # Auth logic
│   ├── models/           # Pydantic models
│   │   ├── user.py       # User models
│   │   ├── creator.py    # Creator models
│   │   └── suggestion.py # Suggestion models
│   └── services/         # Business logic
│       ├── ai_service.py # OpenAI/LangChain
│       └── vector_service.py # Vector operations
├── migrations/           # Database migrations
└── tests/                # Test suite
```

## License

This project is licensed under the MIT License - see the LICENSE file for details.