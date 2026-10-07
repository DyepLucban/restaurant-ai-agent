from fastapi import FastAPI, Request, Depends, HTTPException, UploadFile, File
from routes.seat_routes import router as seats
from agents.orchestrator_agent import run
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

@app.post("/webhook")
async def handle_webhook(request: Request):
    pass

@app.post("/test-agent")
async def test_agent(request: QueryBody):
    uuid = str(uuid4())

    query = request.query
    session_id = request.session_id or uuid

    # return await graph_controller.run_graph(query, session_id)
    embedded_query = await embed_query(query)

    res = await search(embedded_query)

    return {"response": query, "id": session_id}

@app.get("/test_db_call")
async def test_db_call(db: AsyncSession = Depends(get_db)):
    tables = await browse(db)
    return tables

@app.post("/langgraph_test")
async def handle_message(request: QueryBody):
    uuid = str(uuid4())  # Generate a unique session ID for each request

    message = request.query
    session_id = request.session_id or uuid

    res = await graph_controller.run_graph(message, session_id)

    return res

@app.post("/ingest_document")
async def handle_ingest(file: UploadFile = File(...)):
    return await ingest_controller.read_file(file)
