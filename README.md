# Portfolio AI

AI assistant for Syshin's portfolio, powered by LangGraph and deployed on Google Cloud Run.

## Features

- **Blog Search**: RAG-based search over 260+ technical blog posts
- **Two-stage Retrieval**: Efficient summary search → detailed content fetch
- **LangGraph Server API**: Compatible with `@langchain/langgraph-sdk`
- **Streaming Support**: Server-Sent Events (SSE) for real-time responses
- **Supabase Checkpointer**: Persistent conversation memory
- **Comprehensive Logging**: Step-by-step execution tracking

## Getting Started

### 1. Clone with Submodules

This project uses a git submodule for blog content. Clone with:

```bash
git clone --recurse-submodules https://github.com/syshin0116/portfolio-ai.git
```

Or if already cloned:

```bash
git submodule update --init --recursive
```

### 2. Install Dependencies

Using [uv](https://github.com/astral-sh/uv):

```bash
uv sync
```

### 3. Configure Environment

Create a `.env` file:

```bash
cp .env.example .env
```

Required environment variables:

```env
# OpenAI API Key
OPENAI_API_KEY=sk-...

# Supabase (optional, for checkpointer)
SUPABASE_CONNECTION_STRING=postgresql://...

# Logging (optional)
LOG_LEVEL=INFO  # or DEBUG for verbose logging
```

### 4. Run Locally

Using uvicorn:

```bash
uv run uvicorn main:app --reload
```

Or using Docker:

```bash
docker build -t portfolio-ai .
docker run -p 8080:8080 --env-file .env portfolio-ai
```

## Deployment

The application is deployed to Google Cloud Run with automatic builds from the `main` branch.

### How Blog Content is Handled

**Local Development:**
- Blog content is managed as a git submodule
- Clone with `--recurse-submodules` or run `git submodule update --init --recursive`

**Cloud Run/Docker:**
- Cloud Build doesn't support git submodules
- The Dockerfile automatically clones blog content during build:
  ```dockerfile
  RUN if [ -d "data/blog/.git" ]; then \
          cd data/blog && git pull origin main; \
      else \
          mkdir -p data && \
          git clone --depth 1 --branch main https://github.com/syshin0116/syshin0116.github.io.git data/blog; \
      fi
  ```
- This ensures blog content is always included in production deployments
- Blog is cloned fresh on each Cloud Build (always up-to-date)

## API Endpoints

- `GET /` - Health check
- `GET /info` - System information
- `POST /runs/stream` - LangGraph Server API compatible streaming endpoint

### Example Usage

```typescript
import { Client } from "@langchain/langgraph-sdk";

const client = new Client({
  apiUrl: "https://your-app.run.app"
});

const stream = client.runs.stream(
  null, // thread_id (auto-generated if null)
  "agent", // assistant_id
  {
    input: {
      messages: [{ role: "user", content: "AI에 대해 알려줘" }]
    },
    streamMode: "messages"
  }
);

for await (const chunk of stream) {
  console.log(chunk);
}
```

## Project Structure

```
portfolio-ai/
├── src/
│   ├── agent/          # LangGraph agent logic
│   │   ├── graph.py    # Agent graph definition
│   │   └── prompts.py  # System prompts
│   ├── api/            # FastAPI endpoints
│   │   ├── models/     # Pydantic models
│   │   └── routes/     # API routes
│   ├── core/           # Core utilities
│   │   ├── logger.py   # Logging configuration
│   │   └── streaming.py # SSE streaming
│   └── tools/          # Agent tools
│       └── blog/       # Blog search tools
├── data/
│   └── blog/           # Blog submodule (260+ posts)
├── Dockerfile          # Multi-stage Docker build
└── main.py            # FastAPI application entry point
```

## License

MIT

