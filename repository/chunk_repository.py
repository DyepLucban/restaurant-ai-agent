from fastapi import Depends
from schemas.seats_schema import SeatCreate, SeatUpdate
from database.connection import get_db
from sqlalchemy import select, text, Integer, String, Text, Float
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.dialects.postgresql import JSONB
from database.models import chunks
from uuid import uuid4

def base_cols():
    return [
        chunks.Chunk.id,
        chunks.Chunk.uuid,
        chunks.Chunk.content,
        chunks.Chunk.meta,
    ]

# Semantic searching
async def semantic_search(query_vector: list[float], db: AsyncSession = Depends(get_db)):
    distance = chunks.Chunk.embedding.cosine_distance(query_vector)
    rows = (await db.execute(
        select(*base_cols(), (1 - distance).label("similarity"))
        .order_by(distance)
        .limit(20)
    )).mappings().all()

    return [r for r in rows if r["similarity"] >= 0.5]

# Keyword searching
async def keyword_search(db, query_text, limit=20):
    KEYWORD_SQL = text("""
        SELECT id, uuid, content, meta, pdb.score(id) AS bm25
        FROM chunks
        WHERE content ||| CAST(:q AS text)
        ORDER BY bm25 DESC
        LIMIT :limit
    """).columns(id=Integer, uuid=String, content=Text, meta=JSONB, bm25=Float)

    result = await db.execute(KEYWORD_SQL, {"q": query_text, "limit": limit})
    return result.mappings().all()

# Combine semantic and keyword searching (hybrid)
def rrf_merge(*result_lists, k=60):
    scores, items = {}, {}
    for result in result_lists:
        for rank, r in enumerate(result, start=1):
            scores[r["id"]] = scores.get(r["id"], 0.0) + 1.0 / (k + rank)
            items.setdefault(r["id"], r)
    return [(items[i], scores[i]) for i in sorted(scores, key=scores.get, reverse=True)]

async def search(query: str, query_vector: list[float], db: AsyncSession = Depends(get_db)):
    sem = await semantic_search(query_vector, db)
    kw = await keyword_search(db, query)
    
    fused = rrf_merge(sem, kw)[:5]
    if not fused:
        return []

    fused_scores = {r["id"]: s for r, s in fused}
    sections = {
        r["meta"].get("section")
        for r, _ in fused
        if r["meta"] and r["meta"].get("section")
    }

    if not sections:
        return [r for r, _ in fused]

    distance = chunks.Chunk.embedding.cosine_distance(query_vector)
    expanded = (await db.execute(
        select(*base_cols(), (1 - distance).label("similarity"))
        .where(chunks.Chunk.meta["section"].as_string().in_(sections))
        .order_by(distance)
    )).mappings().all()

    return sorted(expanded, key=lambda r: fused_scores.get(r["id"], 0), reverse=True)

async def read():
    pass

async def edit():
    pass

async def add(data: list, db: AsyncSession = Depends(get_db)):
    uuid = str(uuid4())
    chunk = chunks.Chunk(
        uuid=uuid,
        content=data[0],
        meta=data[2],
        embedding=data[1]
    )

    return chunk

async def delete():
    pass