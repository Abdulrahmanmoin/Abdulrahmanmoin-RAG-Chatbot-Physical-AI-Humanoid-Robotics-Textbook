---
title: Physical Humanoid Book RAG Chatbot
emoji: 🤖
colorFrom: blue
colorTo: green
sdk: docker
pinned: false
---

# RAG Chatbot Backend

Backend API for the Physical AI & Humanoid Robotics Book RAG Chatbot. This service handles document retrieval, embedding generation, and response generation while ensuring all responses are grounded in the book content.

## Features

- **Retrieval-Augmented Generation (RAG)**: Answers questions based only on Physical AI & Humanoid Robotics book content
- **Full-book queries**: Search across all book content
- **Selection-based queries**: Answer based only on user-selected text
- **Grounding validation**: Ensures all responses are based on retrieved content
- **Source attribution**: Shows where information comes from in the book
- **Refusal logic**: Declines to answer when context is insufficient

## Prerequisites

- Python 3.11+
- Access to OpenRouter API (supports multiple LLMs including Gemini)
- Qdrant Cloud account
- Neon Serverless PostgreSQL account

## Setup

### 1. Clone the Repository

```bash
git clone <repository-url>
cd <repository-name>
```

### 2. Create Virtual Environment

```bash
cd backend
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
```

### 3. Install Dependencies

```bash
pip install -r requirements.txt
```

### 4. Configure Environment Variables

Copy the `.env` file and update with your credentials:

```bash
cp .env .env.local
```

Edit `.env.local` and add your API keys and configuration:

```env
# Qdrant Configuration
QDRANT_URL=your_qdrant_cloud_url
QDRANT_API_KEY=your_qdrant_api_key
QDRANT_COLLECTION_NAME=book_content

# Database Configuration
NEON_DATABASE_URL=your_neon_postgres_connection_string

# OpenRouter API (Primary LLM service - supports multiple models including Gemini)
OPENROUTER_API_KEY=your_openrouter_api_key_here
# Optional: Specify the model to use (default: google/gemini-pro)
OPENROUTER_MODEL=google/gemini-pro

# Application Configuration
APP_ENV=development
LOG_LEVEL=info
MAX_QUERY_LENGTH=1000
MAX_RESPONSE_TOKENS=500
FRONTEND_URL=http://localhost:3000

# Retrieval Configuration
RETRIEVAL_TOP_K=5
RETRIEVAL_SIMILARITY_THRESHOLD=0.7

# Generation Configuration
GENERATION_TEMPERATURE=0.1
```

## Running the Application

### Start the API Server

```bash
python start_server.py
```

The API will be available at `http://localhost:8000`

### API Documentation

- Interactive docs: `http://localhost:8000/api/docs`
- Alternative docs: `http://localhost:8000/api/redoc`

## Ingesting Book Content

To add book content to the RAG system:

```bash
python -m src.scripts.ingest_documents /path/to/book/content
```

This will:
1. Parse the book content
2. Chunk it into semantically meaningful pieces
3. Generate embeddings using the configured embedding model
4. Store chunks in PostgreSQL and embeddings in Qdrant

## API Endpoints

### Chat Endpoint

`POST /api/chat`

Query the chatbot with a question:

```json
{
  "query": "What are the key principles of humanoid locomotion?",
  "query_type": "full_book",
  "selected_text": "Optional text for selection-based queries"
}
```

**Query Types:**
- `full_book`: Search across all book content
- `selection_based`: Answer based only on selected text

### Health Check

`GET /api/health`

Check if the service is running.

## Environment Variables

| Variable | Description | Default |
|----------|-------------|---------|
| `QDRANT_URL` | Qdrant Cloud URL | - |
| `QDRANT_API_KEY` | Qdrant API key | - |
| `QDRANT_COLLECTION_NAME` | Qdrant collection name | `book_content` |
| `NEON_DATABASE_URL` | PostgreSQL connection string | - |
| `OPENROUTER_API_KEY` | OpenRouter API key | - |
| `OPENROUTER_MODEL` | Model to use (e.g., google/gemini-pro) | `google/gemini-pro` |
| `APP_ENV` | Environment (development/production) | `development` |
| `LOG_LEVEL` | Logging level | `info` |
| `MAX_QUERY_LENGTH` | Maximum query length in characters | `1000` |
| `MAX_RESPONSE_TOKENS` | Maximum response tokens | `500` |
| `FRONTEND_URL` | Frontend URL for CORS | `http://localhost:3000` |
| `RETRIEVAL_TOP_K` | Number of chunks to retrieve | `5` |
| `RETRIEVAL_SIMILARITY_THRESHOLD` | Minimum similarity threshold | `0.7` |
| `GENERATION_TEMPERATURE` | Generation temperature | `0.1` |

## Architecture

The backend follows a service-oriented architecture:

- **Models**: SQLAlchemy and Pydantic models
- **Services**: Business logic (retrieval, embedding, validation, query processing)
- **API**: FastAPI endpoints with proper routing
- **Configuration**: Settings management with environment variables
- **Agents**: RAG agent for controlled generation

## Quality Assurance

The system ensures response quality through:

- **Grounding validation**: Responses must be based on retrieved content
- **Context sufficiency checks**: Refuses to answer if context is insufficient
- **External knowledge detection**: Identifies and prevents external knowledge usage
- **Source attribution**: Shows where information originates

## Development

### Running Tests

```bash
pytest
```

### Code Formatting

```bash
black src/
```

### Linting

```bash
flake8 src/
```

## Deployment

For production deployment:

1. Set `APP_ENV=production` in environment variables
2. Use secure, non-debug settings
3. Ensure proper resource limits and monitoring
4. Set up proper logging aggregation
5. Implement proper backup strategies for the database
