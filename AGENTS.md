# AGENTS.md

Instructions and orientation for AI coding agents working in this repository.

## Project Overview

Restaurant AI Agent — a restaurant customer-assistant service. It is built with:

- **FastAPI** for the HTTP layer and **async SQLAlchemy** (PostgreSQL + pgvector) for storage.
- **LangGraph** to orchestrate multi-step conversations (a router decides where each message goes).
- **LangChain** for the agent loop and the tools agents can call.
- An OpenAI-compatible "runner" model server for the LLM and embedding models (configured via `RUNNER_MODEL*` / `RUNNER_EMBEDDING_MODEL` env vars).

Two capabilities:

- **FAQ** — answer customer questions about the restaurant (menu, hours, policies, …) using a hybrid (semantic + keyword) search over ingested documents.
- **Reservations** — check table availability and book tables.

## Project Structure

```
.
├── main.py                        # FastAPI app and HTTP endpoints (/health, /run-agent, /ingest_document, …)
├── requirements.txt              # Pinned dependencies for the app and services
├── Dockerfile                   # App image (python:3.12-slim); runs `uvicorn main:app`
├── docker-compose.yml           # `app` + `postgres` services
├── .env.example                 # Template for the required environment variables
├── .gitignore
├── others.txt                  # Notes: how to run the evals
├── frontend/                     # Streamlit demo UI
│   ├── app.py                  # Chat + live table floor map + restaurant PDF panel
│   ├── Dockerfile              # UI image (python:3.12-slim); runs streamlit
│   └── requirements.txt        # Frontend-only dependencies (streamlit, requests)
├── agents/                     # LangGraph agent nodes
│   ├── core.py                # run_core(): shared LangChain agent loop (tool calling)
│   ├── orchestrator_agent.py # Router node: intent classification, graph routing
│   ├── faq_agent.py          # FAQ answering via the search_menu_docs tool
│   └── reservation_agent.py  # Reservation handling via the booking tools
├── config/                     # Configuration and prompts
│   ├── settings.py           # Environment variables (DB, models, LangSmith, timezone)
│   └── prompts.py           # All LLM prompts (orchestrator, router, FAQ, reservation, …)
├── controllers/               # FastAPI controllers (HTTP-facing logic)
│   ├── graph_controller.py   # Builds/caches the LangGraph and runs it (run_graph)
│   ├── seats_controller.py   # Seats CRUD
│   ├── table_controller.py   # Tables read endpoints (list + change fingerprint)
│   └── ingest_controller.py  # PDF upload -> chunk -> embed -> store
├── database/                  # Async SQLAlchemy setup and ORM
│   ├── connection.py        # Async engine/session; `get_db` dependency
│   └── models/              # ORM models (users, seats, tables, chunks with pgvector)
├── evals/                     # Evaluation cases and runner
│   ├── run_evals.py
│   └── cases.json
├── repository/               # Data-access layer (SQLAlchemy queries)
│   ├── chunk_repository.py  # Hybrid search: pgvector + BM25, fused with RRF
│   ├── seat_repository.py  # Seats queries
│   └── table_repository.py # Tables queries
├── routes/                   # FastAPI routers (HTTP endpoints)
│   ├── seat_routes.py      # Seats endpoints
│   └── table_routes.py     # Tables endpoints (GET /tables/, GET /tables/version)
├── schemas/                  # Pydantic schemas shared across layers
│   ├── state_schema.py     # LangGraph State (messages, booking_draft, pending_agent, …)
│   ├── route_schema.py     # Route: intent classification output
│   ├── seats_schema.py     # Seat create/read/update schemas
│   ├── tables_schema.py    # Table create/read/update schemas
│   └── base_schema.py      # QueryBody (run-agent request)
└── services/                # Business services
    ├── embedding_service.py      # Embeddings and query embeddings (OpenAIEmbeddings)
    └── document_chunking_service.py  # chunk_document(): PDF text -> section-aware chunks
```

## Running the Project

- The `.venv/` is already provisioned (Python 3.12). Dependencies are listed in `requirements.txt`.
- Configuration is read from the environment: copy `.env.example` to `.env` and fill it in (Postgres connection, runner model, LangSmith). `config/settings.py` loads `.env` on import. `.env` is gitignored.
- Local development (run from the project root, because imports are flat):
  ```
  uvicorn main:app --host 0.0.0.0 --port 8001
  ```
- Docker Compose starts both the app and a `postgres` container (app listens on port 8001):
  ```
  docker compose up
  ```
- Streamlit demo UI — runs as a `frontend` service, so it starts with everything else:
  ```
  docker compose up    # postgres + app (:8001) + UI (:8501)
  ```
  The UI is at http://localhost:8501. It talks to the app over the compose network (`BACKEND_URL=http://app:8001`); no CORS needed since the UI's HTTP calls are made by the Streamlit server process.
- Local UI fallback (no Docker for the frontend):
  ```
  pip install -r frontend/requirements.txt && .venv/bin/streamlit run frontend/app.py
  ```
  Set `BACKEND_URL` (default `http://localhost:8001`), `TABLE_POLL_SECONDS` (default `5`; `0` = manual refresh only), `PDF_ROOT` (where the UI looks for restaurant-info PDFs), and `CHAT_HEIGHT` / `MAP_HEIGHT` (panel heights in px, default `520` — longer content scrolls inside the panel).
- The restaurant info PDF shown in the UI sidebar is baked into the `frontend` image from the project root (`COPY . .`). Note `.dockerignore` keeps `.venv/`, `.git/` and `.env` out of all images; to show updated PDFs without rebuilding, mount `- .:/app:ro` on the `frontend` service (set `PDF_ROOT=/app`).
- Running the evaluations (documented in `others.txt`):
  ```
  docker compose exec app python -m evals.run_evals
  ```

## Request Flow and Agent Flow

1. `POST /run-agent` in `main.py` calls `graph_controller.run_graph(query, session_id)`.
2. `run_graph` invokes the compiled LangGraph (built in `controllers/graph_controller.py`) with a `thread_id`, so conversation memory is kept per session.
3. The graph starts at the **orchestrator_agent** node. It classifies the latest message into an intent (`faq`, `reservation`, `chitchat`, `out_of_scope` — see `config/prompts.py`) and routes the conversation accordingly:
   - `faq_agent` calls `search_menu_docs` and answers only from the tool results.
   - `reservation_agent` checks availability with `search_available_tables` and books with `book_table`.
   - The `pending_agent` state keeps the conversation with the reservation agent while it is gathering (party size, date, …).
   - Everything else ends the conversation with a chitchat/out-of-scope reply.
4. The FAQ and reservation agents both use `agents/core.run_core`, the shared LangChain agent loop. It executes tool calls, enforces call limits (3 tool calls per turn, 4 per run), and records executed tools in the `TOOL_LOG` context variable (used by the evals).
5. Ingesting documents: `POST /ingest_document` extracts text from an uploaded PDF, splits it with `chunk_document` (tagging sections), embeds it, and stores the chunks for later search.

## Conventions

- Flat imports: modules import each other by top-level package name (e.g. `from agents.core import run_core`), so always run code from the project root.
- Async-first: HTTP handlers, repositories, and agent steps are `async`; SQLAlchemy uses the async engine/session from `database/connection.py`.
- Configuration is environment-based (`config/settings.py`); do not hardcode model names, connection strings, or credentials.
- Prompts live in `config/prompts.py` — keep prompt text there rather than in agent code, and keep builder functions (e.g. `build_reservation_prompt()`) next to their usage.
- Schemas are Pydantic models in `schemas/`; the LangGraph state is a `TypedDict` in `schemas/state_schema.py`.
- LangChain tools are async functions decorated with `@tool`; keep their docstrings describing when to call them.
- LangSmith tracing is enabled through `LANGSMITH_*` env vars (`@traceable` is applied in `agents/core.py`).
