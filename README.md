# Restaurant AI Agent

[![Python](https://img.shields.io/badge/python-3.12-blue.svg)](https://www.python.org/downloads/release/python-3120)
[![FastAPI](https://img.shields.io/badge/fastapi-ff2b92.svg?logo=fastapi)](https://fastapi.tiangolo.dev/)
[![LangChain](https://img.shields.io/badge/langchain-1.3-1f6f37.svg?logo=langchain)](https://python.langchain.com/)
[![LangGraph](https://img.shields.io/badge/langgraph-1.2-e56930.svg?logo=langgraph)](https://langchain-ai.github.io/langgraph/)
[![Docker](https://img.shields.io/badge/docker-2496ed.svg?logo=docker)](https://www.docker.com/)
[![PostgreSQL](https://img.shields.io/badge/postgresql-336791.svg?logo=postgresql&logoColor=white)](https://www.postgresql.org/)
[![Streamlit](https://img.shields.io/badge/streamlit-ff4b4b.svg?logo=streamlit&logoColor=white)](https://streamlit.io/)

A restaurant customer-assistant service. It answers customer questions about
the restaurant (menu, opening hours, policies, …) and handles table
reservations, powered by FastAPI, LangGraph, LangChain, and a PostgreSQL
database with pgvector — plus a Streamlit demo UI with a live floor map.

## ✨ Features

- 🧠 **Tool-calling agent** – a lightweight agent loop that lets the LLM decide
  when to call a tool, executes the requested calls, and feeds the results back
  until it produces a final answer.

- 📚 **RAG pipeline** – upload a PDF and its content is parsed, chunked,
  embedded, and stored, so the FAQ agent can answer from your own documents.

- 💬 **Two entry points** – a REST endpoint and a Telegram webhook hook, both
  backed by the same agent.

- 🖥️ **Demo UI (Streamlit)** – a chat panel with in-box "Thinking…" bubbles, a
  live table floor map that refreshes when the database changes, and the
  restaurant info PDF shown in the sidebar — see [Demo UI](#demo-ui).

- 🗃️ **Versioned database** – tables are defined with SQLAlchemy and stored in
  a `pgvector`-enabled PostgreSQL database.

- 🔌 **Easy to extend** – tools are plain async functions decorated with
  `@tool`; adding one only requires registering it in the agent.

## 🧰 Built-in tools

| Tool | Used for |
| --- | --- |
| `search_menu_docs` | FAQ: hybrid (semantic + keyword) search over ingested documents |
| `search_available_tables` | Reservations: check which restaurant tables are available |
| `book_table` | Reservations: book a table for a given date |

## 🏗️ Architecture

```mermaid
flowchart LR
    A["HTTP /run-agent\nor /ingest_document"] --> C["Controllers"]
    S["Streamlit UI\n(frontend/app.py)"] -->|" Calls the\nAPI "| A
    C --> D["graph_controller\nruns the agent graph"]
    D --> E["orchestrator_agent\nroutes the conversation"]
    E --> F["faq_agent\nanswers from the knowledge base"]
    E --> G["reservation_agent\nchecks and books tables"]
    F --> H["run_core\ntool-calling loop"]
    G --> H
    H --> I["Runner LLM\n(OpenAI-compatible server)"]
    H --> R["Embedding service\n(stores & searches vectors)"]
    I --> H
```

Both chat entry points converge on the same graph runner, which binds the
available tools to the LLM and loops — invoking the model, dispatching any
requested tool calls, and feeding the results back — until the model returns a
final answer. The Streamlit UI talks to the same REST layer: it sends chat
messages to `/run-agent` and keeps its floor map in sync by polling
`/tables/version` (and re-fetching `/tables/` only when the database changes).

Ingesting a document converts it into chunks with embeddings that are stored
for retrieval, as described under [Testing](#testing).

## 🚀 Getting started

- **Environment** – Python 3.12 is used (see `Dockerfile`). A virtual environment
  is already provisioned in `.venv/`.

1. **Configure the environment** – copy `.env.example` to `.env` and fill in the
   values (see [Configuration](#configuration)). `config/settings.py` loads `.env`
   when the app starts.

   ```bash
   cp .env.example .env
   ```

2. **Run the app** – either locally:

   ```bash
   uvicorn main:app --host 0.0.0.0 --port 8001
   ```

   or with Docker Compose, which starts the `postgres`, `app`, and `frontend`
   containers in one command:

   ```bash
   docker compose up          # API :8001, demo UI :8501
   ```

3. **Talk to it** – the API is now running. See [API](#api). For the demo
   experience, open http://localhost:8501 and use the chat there — see
   [Demo UI](#demo-ui).

## 🖥️ Demo UI

The Streamlit frontend (`frontend/app.py`) is a demo UI with three parts:

- **Chat panel** – type a message; the agent's reply streams back with an
  in-box "⏳ Thinking…" bubble while the LLM works. The conversation keeps the
  same `session_id`, so the agent remembers earlier turns.
- **Table floor map** – a live grid of the restaurant's tables (available /
  reserved) that polls the database for changes every few seconds, so a booking
  made in the chat (or anywhere) shows up on its own.
- **Restaurant info document** – the sidebar lists every `*.pdf` in the
  project root as the document behind the FAQ answers, with a download button
  and an inline preview.

Run it with `docker compose up` (recommended — see above), or locally:

```bash
pip install -r frontend/requirements.txt
.venv/bin/streamlit run frontend/app.py
```

The UI is configured with environment variables — see the frontend section of
[Configuration](#configuration).


## 🔗 API endpoints

| Method | Path | Description |
| ------ | ---- | ----------- |
| GET | `/health` | Health check. |
| POST | `/webhook` | Telegram webhook hook. Not implemented yet. |
| POST | `/run-agent` | Run the agent for a query and return the reply. |
| POST | `/ingest_document` | Upload a PDF to make its content searchable. |
| GET | `/tables/` | List all restaurant tables (number, capacity, reservation state). |
| GET | `/tables/version` | Cheap change fingerprint (`count`, last write time) for polling clients. |

`POST /run-agent` accepts a JSON body:

```json
{
  "query": "Do you have a table for 4 on Friday?",
  "session_id": "optional-session-id"
}
```

The optional `session_id` selects the conversation memory; otherwise a new id is
generated.

## 🧪 Testing

The evaluation script runs the agent end-to-end against the cases in
`evals/cases.json` and verifies the replies and the tools that were called:

```bash
docker compose exec app python -m evals.run_evals
```

## 🧩 Adding a new tool

1. Create `tools/<name>_tool.py`, write a function, and decorate it with `@tool`
   from `langchain_core.tools`. Give it a clear docstring — that is the only
   description the model sees.

2. Add any required credentials to `config/settings.py` and `.env.example`.

3. Import the tool and add it to the list passed into `run_core` in
   `agents/core.py`.

## 🗂️ Project structure

```text
.
├── main.py                        # FastAPI app and HTTP endpoints
├── requirements.txt              # Pinned dependencies for the app and services
├── Dockerfile                   # App image (python:3.12-slim); runs `uvicorn main:app`
├── docker-compose.yml           # `app` + `postgres` + `frontend` services
├── .env.example                 # Template for the required environment variables
├── .dockerignore                # Keeps .venv/.git/.env out of the images
├── .gitignore
├── frontend/                     # Streamlit demo UI
│   ├── app.py                  # Chat + live table floor map + restaurant PDF panel
│   ├── Dockerfile              # UI image; `streamlit run frontend/app.py`
│   └── requirements.txt        # Frontend-only dependencies (streamlit, requests)
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
│   ├── table_controller.py   # Tables read endpoints (list + change fingerprint)
│   └── ingest_controller.py  # PDF upload -> chunk -> embed -> store
├── database/                  # Async SQLAlchemy setup and ORM
│   ├── connection.py        # Async engine/session
│   └── models/              # Restaurant tables and ingested chunks
├── routes/                    # FastAPI routers
│   ├── seat_routes.py         # Seats endpoints
│   └── table_routes.py        # Tables endpoints (list + change fingerprint)
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

## ⚙️ Configuration

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
| `LANGSMITH_API_KEY`, `LANGSMITH_PROJECT`, `LANGSMITH_ENDPOINT` | LangSmith credentials and project. |

**Frontend (Streamlit UI only):**

| Variable | Purpose |
| -------- | ------- |
| `BACKEND_URL` | Base URL of the API (compose default: `http://app:8001`). |
| `TABLE_POLL_SECONDS` | How often the floor map checks the DB for changes (default `5`; `0` = manual refresh only). |
| `PDF_ROOT` | Where the UI discovers restaurant-info PDFs (defaults to the project root). |
| `CHAT_HEIGHT`, `MAP_HEIGHT` | Panel heights in px (default `520`); longer content scrolls inside the panel. |
