from fastapi import FastAPI, Request, Depends, UploadFile, File
from routes.seat_routes import router as seats
from schemas.base_schema import QueryBody
from repository.table_repository import browse
from uuid import uuid4

from sqlalchemy.ext.asyncio import AsyncSession
from database.connection import get_db

from controllers import graph_controller, ingest_controller
from services.embedding_service import embed_query

from repository.chunk_repository import search

app = FastAPI()
app.include_router(seats)

@app.get("/health")
def check_health():
    return {
        "status": 200,
        "is_healthy": True
    }

# Run the agent via telegram webhook
@app.post("/webhook")
async def handle_webhook(request: Request):
    pass

# Run the agent via API
@app.post("/run-agent")
async def run_agent(request: QueryBody):
    uuid = str(uuid4())

    query = request.query
    session_id = request.session_id or uuid

    return await graph_controller.run_graph(query, session_id)

# Ingest restaurant's documentation
@app.post("/ingest_document")
async def handle_ingest(file: UploadFile = File(...)):
    return await ingest_controller.read_file(file)
