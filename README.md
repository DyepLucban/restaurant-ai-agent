# Restaurant AI Agent

A restaurant customer-assistant service. It answers customer questions about the
restaurant (menu, opening hours, policies, …) and handles table reservations,
powered by a combination of FastAPI, LangGraph, LangChain, and a PostgreSQL
database with pgvector.

## Features

- **FAQ** – answers questions about the restaurant using a hybrid (semantic +
  keyword) search over the ingested documents.
- **Reservations** – checks which restaurant tables are available, and books
  them for a given date.
- **Conversation memory** – each request is tied to a session, so follow-up
  messages keep the context of the conversation.
- **Document ingestion** – PDFs can be uploaded; their content is split into
  sections, embedded, and becomes searchable by the FAQ agent.

## How it works

The application is a FastAPI service built around a LangGraph state graph.

1. A message arrives through `POST /run-agent` (or through the Telegram webhook
   hook, once implemented). The message and the session id are passed to the
   graph runner.
2. The graph starts at the **orchestrator agent**, which classifies the latest
   message into one of four intents:
   - `faq` – questions about the restaurant,
   - `reservation` – checking availability or booking a table,
   - `chitchat` / `out_of_scope` – everything else.
   It then routes the conversation to the matching agent, or ends it with a
   reply.
3. The **FAQ agent** searches the knowledge base with the `search_menu_docs`
   tool and answers using only the retrieved information.
4. The **reservation agent** searches for available tables with
   `search_available_tables` and books them with `book_table`.
5. Both agents use the shared LangChain loop in `agents/core.py`, which executes
   the requested tools and enforces call limits.
6. When documents are ingested (`POST /ingest_document`), they are chunked,
   embedded, and stored so that step 3 can answer questions about them.

## Project structure

```
.
├── main.py                        # FastAPI app and HTTP endpoints
├── requirements.txt              # Pinned dependencies for the app and services
├── Dockerfile                   # App image (python:3.12-slim); runs `uvicorn main:app`
├── docker-compose.yml           # `app` + `postgres` services
├── .env.example                 # Template for the required environment variables
├── .gitignore
├── agents/                     # LangGraph agent nodes
│   ├── core.py                # Shared LangChain agent loop (run_core)
│   ├── orchestrator_agent.py # Intent router for the conversation
│   ├── faq_agent.py         # Answers FAQ using the knowledge base
│   └── reservation_agent.py  # Handles reservations and bookings
├── config/                     # Configuration and prompts
│   ├── settings.py          # Environment variables
│   └── prompts.py          # All LLM prompts
├── controllers/               # HTTP-facing logic
│   ├── graph_controller.py   # Builds/caches the agent graph; runs it
│   └── ingest_controller.py  # PDF upload -> chunk -> embed -> store
├── database/                  # Async SQLAlchemy setup and ORM
│   ├── connection.py        # Async engine/session
│   └── models/              # Restaurant tables and ingested chunks
├── evals/                     # Evaluation cases and runner
│   ├── run_evals.py
│   └── cases.json
├── repository/               # Data-access layer
│   ├── chunk_repository.py  # Hybrid (semantic + keyword) search over chunks
│   └── table_repository.py # Restaurant table queries (availability, booking)
└── services/                # Business services
    ├── embedding_service.py      # Embeddings and query embeddings
    └── document_chunking_service.py  # Split uploaded PDFs into searchable chunks
```

## Getting started

- **Environment** – Python 3.12 is used (see `Dockerfile`). A virtual environment
  is already provisioned in `.venv/`.
- **Dependencies** – install everything listed in `requirements.txt`:
  ```
  pip install -r requirements.txt
  ```
- **Configuration** – copy `.env.example` to `.env` and fill in the values
  (see [Configuration](#configuration)). `config/settings.py` loads `.env` when
  the app starts.

## Running

- **Local** – run the API from the project root:
  ```
  uvicorn main:app --host 0.0.0.0 --port 8001
  ```
- **Docker** – `docker compose up` starts both the app and a `postgres`
  container; the app is then available on port 8001.

## API

| Method | Path | Description |
| ------ | ---- | ----------- |
| GET | `/health` | Health check. |
| POST | `/webhook` | Telegram webhook hook. Not implemented yet. |
| POST | `/run-agent` | Run the agent for a query and return the reply. |
| POST | `/ingest_document` | Upload a PDF to make its content searchable. |

`POST /run-agent` accepts a JSON body:

```json
{
  "query": "Do you have a table for 4 on Friday?",
  "session_id": "optional-session-id"
}
```

The optional `session_id` selects the conversation memory; otherwise a new id is
generated.

## Testing

The evaluation script runs the agent end-to-end against the cases in
`evals/cases.json` and verifies the replies and the tools that were called:

```
docker compose exec app python -m evals.run_evals
```

## Configuration

All configuration is read from environment variables (see `.env.example`):

| Variable | Purpose |
| -------- | ------- |
| `TIMEZONE` | Timezone used when resolving dates in prompts. |
| `POSTGRES_HOST`, `POSTGRES_PORT`, `POSTGRES_USER`, `POSTGRES_PASSWORD`, `POSTGRES_DB` | PostgreSQL connection. |
| `RUNNER_MODEL_BASE_URL` | Base URL of the OpenAI-compatible model runner. |
| `RUNNER_MODEL` | Model used by the agents. |
| `RUNNER_EMBEDDING_MODEL` | Model used for embeddings. |
| `EMBEDDING_DIM` | Dimension of the embedding vectors. |
| `LANGSMITH_TRACING` | Enables LangSmith tracing, if desired. |
| `LANGSMITH_API_KEY` / `LANGSMITH_PROJECT` / `LANGSMITH_ENDPOINT` | LangSmith credentials and project. |
