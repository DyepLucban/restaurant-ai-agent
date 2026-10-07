from langchain_core.tools import tool
from services.embedding_service import embed_query
from repository.chunk_repository import search
from database.connection import SessionAsync

@tool
async def search_menu_docs(query: str) -> str:
    """Search the restaurant's knowledge base for information about Amara Kusina.

    Covers: menu items and prices (appetizers, main courses, vegetarian options,
    desserts, drinks), allergens, opening hours, location, parking, and payment
    methods.

    Use a specific, self-contained query (e.g. "main courses", "parking",
    "opening hours on Sunday"). One search is usually enough, so do not repeat
    the tool with rephrased queries for the same question.
    """

    embedded_query = await embed_query(query)

    async with SessionAsync() as db:
        rows = await search(embedded_query, db)

    for r in rows:
        print(f"{r['similarity']:.3f}  {r['content'][:60]}")

    hits = [f"[{r['id']}] {r['content']}" for r in rows]

    return "\n\n".join(hits) or "No matching documents found."