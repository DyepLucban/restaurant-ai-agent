from fastapi import FastAPI, Request, UploadFile, File
from routes.seat_routes import router as seats
from routes.table_routes import router as tables
from schemas.base_schema import QueryBody
from uuid import uuid4

from controllers import graph_controller, ingest_controller

app = FastAPI()
app.include_router(seats)
app.include_router(tables)

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
